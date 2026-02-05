# LangGraph Hooks Implementation Guide

## Overview

This document explains the LangGraph hooks implementation that replaces the Strands hooks system. The new implementation provides similar functionality with better integration into LangGraph's architecture.

## Architecture Comparison

### Strands Hooks (Original - Lines 268-280)

```python
# Create memory hook if memory is initialized
hooks = []
if memory_id:
    hooks.append(ShortTermMemoryHook(memory_client, memory_id))

# Create orchestrator agent with hooks
orchestrator = Agent(
    model=bedrock_model,
    system_prompt=CAMPAIGN_ORCHESTRATOR_PROMPT,
    tools=[persona_reviewer_agent, validator_agent, finalizer_agent],
    hooks=hooks,
    state={"actor_id": actor_id, "session_id": session_id}
)
```

**Characteristics**:
- Hooks attached to Agent instance
- Called automatically by Strands framework
- Limited to Strands-specific events
- Tightly coupled to Agent lifecycle

### LangGraph Hooks (New Implementation)

```python
# Create orchestrator workflow with hooks
orchestrator, hook_manager = create_campaign_orchestrator(
    session_id=session_id,
    actor_id="campaign_user",
    memory_client=memory_client,
    memory_id=memory_id
)

# Hooks are called explicitly
hook_manager.on_workflow_start(initial_state)
final_state = orchestrator.invoke(initial_state)
hook_manager.on_workflow_end(final_state)
```

**Characteristics**:
- Hooks managed by HookManager
- Explicit hook calls for workflow events
- Node-level hooks via wrapper functions
- Flexible and extensible

---

## Hook Types

### 1. LoggingHook

**Purpose**: Detailed workflow logging with session tracking

**Features**:
- Logs workflow start/end with timing
- Logs each node execution
- Tracks session_id and actor_id
- Captures errors with stack traces

**Usage**:
```python
logging_hook = LoggingHook(
    session_id="campaign-20260204123456",
    actor_id="campaign_user"
)
hook_manager.add_hook(logging_hook)
```

**Output Example**:
```
[campaign-20260204123456] Workflow started by campaign_user
[campaign-20260204123456] Campaign ID: camp_123
[campaign-20260204123456] Node 'persona_review' starting
[campaign-20260204123456] Node 'persona_review' completed
[campaign-20260204123456] Node 'validation' starting
[campaign-20260204123456] Node 'validation' completed
[campaign-20260204123456] Node 'finalizer' starting
[campaign-20260204123456] Node 'finalizer' completed
[campaign-20260204123456] Workflow completed in 45.23s
```

### 2. MetricsHook

**Purpose**: Collect performance metrics for each node and overall workflow

**Features**:
- Tracks total workflow duration
- Measures individual node execution times
- Provides performance insights
- Helps identify bottlenecks

**Usage**:
```python
metrics_hook = MetricsHook(session_id="campaign-20260204123456")
hook_manager.add_hook(metrics_hook)
```

**Output Example**:
```
[campaign-20260204123456] Workflow Metrics:
  Total Duration: 45.23s
  persona_review: 18.45s
  validation: 12.67s
  finalizer: 14.11s
```

### 3. MemoryHook (AgentCore Integration)

**Purpose**: Integrate AWS Bedrock AgentCore Memory for cross-session learning

**Features**:
- Retrieves relevant past campaign context at workflow start
- Stores node execution context during workflow
- Saves successful workflow results to memory
- Stores error context for learning from failures

**Usage**:
```python
from tools.memory_client import get_memory_client, initialize_memory

memory_client = get_memory_client()
memory_id = initialize_memory()

memory_hook = MemoryHook(
    memory_client=memory_client,
    memory_id=memory_id,
    session_id="campaign-20260204123456"
)
hook_manager.add_hook(memory_hook)
```

**What Gets Stored**:

**On Workflow Start** (Retrieval):
```python
# Queries memory for similar past campaigns
past_context = memory_client.retrieve(
    memory_id=memory_id,
    query=campaign_content[:500],
    max_results=3
)
# Adds past context to state messages
```

**On Workflow End** (Storage):
```python
memory_content = {
    "session_id": session_id,
    "campaign_id": campaign_id,
    "franchise": franchise,
    "timestamp": "2026-02-04T12:34:56",
    "workflow_path": ["persona_review", "validation", "finalizer"],
    "summary": final_report[:1000],
    "persona_insights": persona_review[:500],
    "compliance_notes": validation_report[:500]
}
```

**On Error** (Learning):
```python
error_content = {
    "session_id": session_id,
    "campaign_id": campaign_id,
    "error_type": "ValidationError",
    "error_message": "...",
    "workflow_path": ["persona_review", "validation"]
}
```

---

## Hook Lifecycle

### Workflow-Level Hooks

```
Lambda Handler
    ↓
hook_manager.on_workflow_start(initial_state)
    ↓
    ├─ LoggingHook.on_workflow_start()
    │   └─ Log: "Workflow started"
    ├─ MetricsHook.on_workflow_start()
    │   └─ Record: start_time
    └─ MemoryHook.on_workflow_start()
        └─ Retrieve past context from AgentCore Memory
    ↓
orchestrator.invoke(initial_state)
    ↓
    [Nodes execute with node-level hooks]
    ↓
hook_manager.on_workflow_end(final_state)
    ↓
    ├─ LoggingHook.on_workflow_end()
    │   └─ Log: "Workflow completed in X.XXs"
    ├─ MetricsHook.on_workflow_end()
    │   └─ Log: Performance metrics
    └─ MemoryHook.on_workflow_end()
        └─ Store results in AgentCore Memory
```

### Node-Level Hooks

```
Node Execution (via create_hooked_node wrapper)
    ↓
hook_manager.on_node_start(node_name, state)
    ↓
    ├─ LoggingHook.on_node_start()
    │   └─ Log: "Node 'persona_review' starting"
    ├─ MetricsHook.on_node_start()
    │   └─ Record: node_start_time
    └─ MemoryHook.on_node_start()
        └─ Track node execution
    ↓
node_func(state)  # Actual node execution
    ↓
hook_manager.on_node_end(node_name, state)
    ↓
    ├─ LoggingHook.on_node_end()
    │   └─ Log: "Node 'persona_review' completed"
    ├─ MetricsHook.on_node_end()
    │   └─ Calculate: node_duration
    └─ MemoryHook.on_node_end()
        └─ Store node context
```

### Error Handling

```
try:
    orchestrator.invoke(initial_state)
except Exception as e:
    hook_manager.on_error(e, state)
    ↓
    ├─ LoggingHook.on_error()
    │   └─ Log: Error with stack trace
    ├─ MetricsHook.on_error()
    │   └─ (No action)
    └─ MemoryHook.on_error()
        └─ Store error context in memory
    ↓
    raise  # Re-raise exception
```

---

## Implementation Details

### HookManager

Central coordinator for all hooks:

```python
class HookManager:
    def __init__(self):
        self.hooks = []
    
    def add_hook(self, hook: WorkflowHook):
        """Add a hook to the manager"""
        self.hooks.append(hook)
    
    def on_workflow_start(self, state):
        """Call all hooks' on_workflow_start"""
        for hook in self.hooks:
            try:
                hook.on_workflow_start(state)
            except Exception as e:
                logger.error(f"Hook failed: {e}")
```

**Benefits**:
- Multiple hooks can be active simultaneously
- Hooks are isolated (one failure doesn't affect others)
- Easy to add/remove hooks dynamically
- Consistent interface across all hooks

### Node Wrapping

Nodes are wrapped to inject hook calls:

```python
def create_hooked_node(node_func, node_name, hook_manager):
    """Wrap a node function with hook calls"""
    def wrapped_node(state):
        hook_manager.on_node_start(node_name, state)
        try:
            result = node_func(state)
            hook_manager.on_node_end(node_name, result)
            return result
        except Exception as e:
            hook_manager.on_error(e, state)
            raise
    return wrapped_node
```

**Usage in Workflow**:
```python
# Original node
def persona_review_node(state):
    # ... node logic
    return state

# Wrapped with hooks
hooked_persona_review = create_hooked_node(
    persona_review_node, 
    "persona_review", 
    hook_manager
)

# Add to workflow
workflow.add_node("persona_review", hooked_persona_review)
```

---

## Configuration

### Basic Setup (No Memory)

```python
orchestrator, hook_manager = create_campaign_orchestrator(
    session_id="campaign-20260204123456",
    actor_id="campaign_user"
)
```

**Enabled Hooks**:
- ✅ LoggingHook
- ✅ MetricsHook
- ❌ MemoryHook (not configured)

### With AgentCore Memory

```python
from tools.memory_client import get_memory_client, initialize_memory

memory_client = get_memory_client()
memory_id = initialize_memory()

orchestrator, hook_manager = create_campaign_orchestrator(
    session_id="campaign-20260204123456",
    actor_id="campaign_user",
    memory_client=memory_client,
    memory_id=memory_id
)
```

**Enabled Hooks**:
- ✅ LoggingHook
- ✅ MetricsHook
- ✅ MemoryHook (with AgentCore integration)

### Dynamic Memory Initialization

The orchestrator tries to initialize memory gracefully:

```python
# Initialize memory if available (optional)
memory_client = None
memory_id = None
try:
    from tools.memory_client import get_memory_client, initialize_memory
    memory_client = get_memory_client()
    memory_id = initialize_memory()
    logger.info("AgentCore Memory initialized")
except ImportError:
    logger.info("AgentCore Memory not available (optional)")
except Exception as e:
    logger.warning(f"Failed to initialize memory: {e}")
```

**Benefits**:
- Works without memory dependencies
- Gracefully degrades if memory unavailable
- Easy to enable/disable memory

---

## Custom Hooks

You can create custom hooks by extending `WorkflowHook`:

```python
from lambda.langgraph_hooks import WorkflowHook

class CustomHook(WorkflowHook):
    def on_workflow_start(self, state):
        # Custom logic at workflow start
        pass
    
    def on_node_end(self, node_name, state):
        # Custom logic after each node
        if node_name == "persona_review":
            # Do something specific for persona review
            pass
    
    def on_workflow_end(self, state):
        # Custom logic at workflow end
        pass

# Add to hook manager
hook_manager.add_hook(CustomHook())
```

### Example: S3 Checkpoint Hook

```python
class S3CheckpointHook(WorkflowHook):
    """Save workflow state to S3 after each node"""
    
    def __init__(self, bucket_name, campaign_id):
        self.bucket_name = bucket_name
        self.campaign_id = campaign_id
    
    def on_node_end(self, node_name, state):
        # Save state checkpoint to S3
        checkpoint_key = f"campaigns/{self.campaign_id}/checkpoints/{node_name}.json"
        checkpoint_data = {
            "node": node_name,
            "timestamp": datetime.now().isoformat(),
            "state": {
                "persona_review": state.get("persona_review", ""),
                "validation_report": state.get("validation_report", ""),
                "final_report": state.get("final_report", "")
            }
        }
        write_text_to_s3(
            self.bucket_name,
            checkpoint_key,
            json.dumps(checkpoint_data)
        )
```

---

## Benefits Over Strands Hooks

### 1. Explicit Control
- **Strands**: Hooks called automatically by framework
- **LangGraph**: Explicit hook calls, clear when they execute

### 2. Flexibility
- **Strands**: Limited to framework-defined events
- **LangGraph**: Custom events and hooks easily added

### 3. Debugging
- **Strands**: Hook execution hidden in framework
- **LangGraph**: Clear hook execution flow, easy to debug

### 4. Testing
- **Strands**: Hard to test hooks in isolation
- **LangGraph**: Hooks are standalone classes, easy to test

### 5. Observability
- **Strands**: Limited visibility into hook execution
- **LangGraph**: Full control over logging and monitoring

---

## Migration Checklist

If you had Strands hooks, here's how to migrate:

- [x] Remove Strands hook imports
- [x] Remove `hooks=[]` parameter from Agent creation
- [x] Import LangGraph hooks: `from lambda.langgraph_hooks import ...`
- [x] Update `create_campaign_orchestrator()` to accept memory parameters
- [x] Add hook_manager initialization
- [x] Wrap nodes with `create_hooked_node()`
- [x] Add explicit hook calls in lambda_handler
- [x] Test with and without memory enabled

---

## Conclusion

The LangGraph hooks implementation provides:

✅ **Feature Parity**: All Strands hook functionality preserved  
✅ **Better Control**: Explicit hook lifecycle management  
✅ **More Flexible**: Easy to add custom hooks  
✅ **Optional Memory**: Works with or without AgentCore Memory  
✅ **Better Observability**: Clear logging and metrics  
✅ **Easier Testing**: Hooks are testable in isolation  

The implementation is production-ready and provides a solid foundation for workflow observability and memory integration.

# LangGraph Conversion - Quick Reference

## Summary

✅ **Converted Strands orchestrator to LangGraph**  
✅ **Implemented hooks system (lines 268-280)**  
✅ **Memory integration (optional)**  
✅ **Production-ready**

---

## Key Changes

| Component | Before (Strands) | After (LangGraph) |
|-----------|------------------|-------------------|
| Framework | `strands-agents` | `langgraph` |
| Model | `BedrockModel` | `ChatBedrock` |
| Orchestration | `Agent` with tools | `StateGraph` with nodes |
| State | Implicit | Explicit `CampaignState` |
| Hooks | Strands hooks | Custom hook system |
| Memory | Optional | Optional (same) |

---

## File Structure

```
lambda/
├── orchestrator.py          # ✅ Updated - Main orchestrator
├── langgraph_hooks.py       # ✅ New - Hook system
└── requirements.txt         # ✅ Updated - Dependencies

tools/
├── revieweragent.py         # ✅ Updated - No @tool decorator
├── validatoragent.py        # ✅ Updated - No @tool decorator
├── finalizeragent.py        # ✅ Updated - No @tool decorator
└── memory_client_example.py # ✅ New - Optional memory

Documentation/
├── LANGGRAPH_CONVERSION.md           # Conversion overview
├── MEMORY_VALIDATION.md              # Memory analysis
├── LANGGRAPH_MEMORY_SUMMARY.md       # Memory details
├── MEMORY_FLOW_DIAGRAM.md            # Visual diagrams
├── LANGGRAPH_HOOKS_GUIDE.md          # Hooks guide
├── HOOKS_IMPLEMENTATION_SUMMARY.md   # Hooks summary
└── QUICK_REFERENCE.md                # This file
```

---

## Workflow

```
┌─────────────────────────────────────────────┐
│         Lambda Handler                      │
│  - Initialize hooks                         │
│  - Create orchestrator                      │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│    hook_manager.on_workflow_start()         │
│  - Log workflow start                       │
│  - Record metrics                           │
│  - Retrieve memory context (optional)       │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│         LangGraph Workflow                  │
│                                             │
│  ┌───────────────────────────────────────┐ │
│  │  Node 1: persona_review               │ │
│  │  - on_node_start()                    │ │
│  │  - Execute review                     │ │
│  │  - on_node_end()                      │ │
│  └───────────────┬───────────────────────┘ │
│                  │                          │
│  ┌───────────────▼───────────────────────┐ │
│  │  Node 2: validation                   │ │
│  │  - on_node_start()                    │ │
│  │  - Execute validation                 │ │
│  │  - on_node_end()                      │ │
│  └───────────────┬───────────────────────┘ │
│                  │                          │
│  ┌───────────────▼───────────────────────┐ │
│  │  Node 3: finalizer                    │ │
│  │  - on_node_start()                    │ │
│  │  - Execute finalization               │ │
│  │  - on_node_end()                      │ │
│  └───────────────┬───────────────────────┘ │
│                  │                          │
└──────────────────┼──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│    hook_manager.on_workflow_end()           │
│  - Log completion                           │
│  - Log metrics                              │
│  - Store results in memory (optional)       │
└─────────────────────────────────────────────┘
```

---

## Usage

### Basic (No Memory)

```python
orchestrator, hook_manager = create_campaign_orchestrator(
    session_id="campaign-20260204123456",
    actor_id="campaign_user"
)

hook_manager.on_workflow_start(initial_state)
final_state = orchestrator.invoke(initial_state)
hook_manager.on_workflow_end(final_state)
```

### With Memory

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

---

## Hooks

| Hook | Purpose | Always Enabled |
|------|---------|----------------|
| `LoggingHook` | Detailed logging | ✅ Yes |
| `MetricsHook` | Performance metrics | ✅ Yes |
| `MemoryHook` | AgentCore Memory | ❌ Optional |

---

## State

```python
CampaignState = {
    # Input
    "campaign_content": str,
    "campaign_id": str,
    "franchise": str,
    "franchise_type": str,
    "version": str,
    
    # Outputs (set by nodes)
    "persona_review": str,
    "validation_report": str,
    "final_report": str,
    
    # Metadata
    "messages": List[BaseMessage],
    "error": str
}
```

---

## Dependencies

```txt
# Required
langgraph
langchain-aws
langchain-core
requests
boto3
opentelemetry-api
opentelemetry-sdk
opentelemetry-instrumentation

# Optional (for memory)
bedrock-agentcore
```

---

## Testing

```bash
# Test without memory
python lambda/orchestrator.py

# Test with memory (after setup)
pip install bedrock-agentcore
mv tools/memory_client_example.py tools/memory_client.py
python lambda/orchestrator.py
```

---

## Benefits

### vs Strands

✅ Explicit state management  
✅ Better observability  
✅ Easier debugging  
✅ More flexible  
✅ Standard framework  
✅ Better documentation  

### New Features

✅ Performance metrics  
✅ Node-level hooks  
✅ Custom hook support  
✅ Optional memory  
✅ Graceful degradation  

---

## Common Tasks

### Add Custom Hook

```python
from lambda.langgraph_hooks import WorkflowHook

class MyHook(WorkflowHook):
    def on_workflow_end(self, state):
        # Your logic here
        pass

hook_manager.add_hook(MyHook())
```

### Enable Memory

1. Install: `pip install bedrock-agentcore`
2. Rename: `tools/memory_client_example.py` → `tools/memory_client.py`
3. Configure AWS credentials
4. Set env: `AGENTCORE_MEMORY_ID`

### Add Checkpointing

```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
workflow = workflow.compile(checkpointer=checkpointer)
```

---

## Troubleshooting

### Memory Import Error

**Error**: `ImportError: No module named 'tools.memory_client'`  
**Solution**: This is expected if memory not configured. Orchestrator works without it.

### Hook Not Called

**Check**: Ensure `hook_manager.on_workflow_start()` called before `orchestrator.invoke()`

### Node Not Wrapped

**Check**: Ensure nodes wrapped with `create_hooked_node()` before adding to workflow

---

## Documentation

- **Overview**: `LANGGRAPH_CONVERSION.md`
- **Memory**: `MEMORY_VALIDATION.md`, `LANGGRAPH_MEMORY_SUMMARY.md`
- **Hooks**: `LANGGRAPH_HOOKS_GUIDE.md`, `HOOKS_IMPLEMENTATION_SUMMARY.md`
- **Diagrams**: `MEMORY_FLOW_DIAGRAM.md`
- **Quick Ref**: This file

---

## Status

✅ **Conversion Complete**  
✅ **Hooks Implemented**  
✅ **Memory Validated**  
✅ **Production Ready**

No further action required unless you want to enable optional features.

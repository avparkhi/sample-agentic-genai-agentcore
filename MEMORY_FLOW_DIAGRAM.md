# Memory Flow Diagram - LangGraph Implementation

## Workflow Execution Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Lambda Handler                               │
│  - Receives campaign_id and s3_key                                  │
│  - Reads campaign content from S3                                   │
│  - Creates initial CampaignState                                    │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    LangGraph Workflow                                │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │  Node 1: persona_review_node                               │   │
│  │  ┌──────────────────────────────────────────────────────┐ │   │
│  │  │ 1. Generate random persona_id = "persona_023"        │ │   │
│  │  │ 2. set_current_persona_id("persona_023")             │ │   │
│  │  │    └─> Persona Store (Global)                        │ │   │
│  │  │ 3. Call ChatBedrock to generate review               │ │   │
│  │  │ 4. Save to S3: .../persona_023/campaign_review.md    │ │   │
│  │  │ 5. state["persona_review"] = review_text             │ │   │
│  │  └──────────────────────────────────────────────────────┘ │   │
│  └────────────────────────────────────────────────────────────┘   │
│                             │                                        │
│                             │ state passed ↓                         │
│                             ▼                                        │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │  Node 2: validation_node                                   │   │
│  │  ┌──────────────────────────────────────────────────────┐ │   │
│  │  │ 1. persona_id = get_current_persona_id()             │ │   │
│  │  │    └─> Persona Store (Global) returns "persona_023"  │ │   │
│  │  │ 2. Read state["campaign_content"]                    │ │   │
│  │  │ 3. Call ChatBedrock to generate validation           │ │   │
│  │  │ 4. Save to S3: .../persona_023/validation_report.md  │ │   │
│  │  │ 5. state["validation_report"] = validation_text      │ │   │
│  │  └──────────────────────────────────────────────────────┘ │   │
│  └────────────────────────────────────────────────────────────┘   │
│                             │                                        │
│                             │ state passed ↓                         │
│                             ▼                                        │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │  Node 3: finalizer_node                                    │   │
│  │  ┌──────────────────────────────────────────────────────┐ │   │
│  │  │ 1. persona_id = get_current_persona_id()             │ │   │
│  │  │    └─> Persona Store (Global) returns "persona_023"  │ │   │
│  │  │ 2. Read state["campaign_content"]                    │ │   │
│  │  │ 3. Read state["persona_review"]                      │ │   │
│  │  │ 4. Read state["validation_report"]                   │ │   │
│  │  │ 5. Call ChatBedrock to synthesize final report       │ │   │
│  │  │ 6. Save to S3: .../persona_023/final_campaign.md     │ │   │
│  │  │ 7. state["final_report"] = final_text                │ │   │
│  │  └──────────────────────────────────────────────────────┘ │   │
│  └────────────────────────────────────────────────────────────┘   │
│                             │                                        │
│                             ▼                                        │
│                           END                                        │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Return final_state                                │
│  - final_report                                                      │
│  - persona_review                                                    │
│  - validation_report                                                 │
└─────────────────────────────────────────────────────────────────────┘
```

## State Management Details

### LangGraph State (Explicit)

```python
CampaignState = {
    # Input (set by Lambda handler)
    "campaign_content": "...",      # From S3
    "campaign_id": "camp_123",      # From request
    "franchise": "EA Sports FC",
    "franchise_type": "Sports",
    "version": "v1",
    
    # Workflow outputs (set by nodes)
    "persona_review": "",           # Set by node 1
    "validation_report": "",        # Set by node 2
    "final_report": "",             # Set by node 3
    
    # Metadata
    "messages": [...],              # Workflow messages
    "error": ""                     # Error tracking
}
```

**Flow**:
```
Initial State → Node 1 → Updated State → Node 2 → Updated State → Node 3 → Final State
```

### Persona Store (Implicit)

```python
# Global singleton
_persona_store = {
    "default": "persona_023"  # Set by node 1, read by nodes 2 & 3
}
```

**Why Separate?**
- Used only for S3 path construction
- Not part of main workflow logic
- Thread-safe with locks
- Simple string value

## Memory Comparison

### What Strands Did (Original)

```
┌─────────────────────────────────────────────────────────────┐
│  Orchestrator Agent                                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  System Prompt: "You have 3 tools..."                  │ │
│  │  Tools: [persona_reviewer, validator, finalizer]       │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  Agent decides: "I'll call persona_reviewer first"          │
│         ↓                                                    │
│  Tool Call: persona_reviewer(campaign_content)              │
│         ↓                                                    │
│  Tool Result: {...persona_review...}                        │
│         ↓                                                    │
│  Agent decides: "Now I'll call validator"                   │
│         ↓                                                    │
│  Tool Call: validator(campaign_content)                     │
│         ↓                                                    │
│  Tool Result: {...validation_report...}                     │
│         ↓                                                    │
│  Agent decides: "Now I'll call finalizer"                   │
│         ↓                                                    │
│  Tool Call: finalizer(content, review, validation)          │
│         ↓                                                    │
│  Final Response: {...final_report...}                       │
└─────────────────────────────────────────────────────────────┘

State Management: ❌ Hidden inside Agent
Persona Store:    ✅ Used for persona_id
```

### What LangGraph Does (New)

```
┌─────────────────────────────────────────────────────────────┐
│  StateGraph Workflow                                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Node: persona_review_node                             │ │
│  │  Input: state                                          │ │
│  │  Output: state with persona_review added              │ │
│  └────────────────────────────────────────────────────────┘ │
│         ↓ (explicit edge)                                    │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Node: validation_node                                 │ │
│  │  Input: state (has campaign_content, persona_review)   │ │
│  │  Output: state with validation_report added            │ │
│  └────────────────────────────────────────────────────────┘ │
│         ↓ (explicit edge)                                    │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Node: finalizer_node                                  │ │
│  │  Input: state (has all previous outputs)               │ │
│  │  Output: state with final_report added                 │ │
│  └────────────────────────────────────────────────────────┘ │
│         ↓ (explicit edge)                                    │
│       END                                                    │
└─────────────────────────────────────────────────────────────┘

State Management: ✅ Explicit in CampaignState
Persona Store:    ✅ Used for persona_id
```

## S3 Storage Pattern

All outputs are saved to S3 with consistent paths:

```
s3://bucket/campaigns/{campaign_id}/
├── brief.md                                    # Input (uploaded by user)
├── status.json                                 # Status tracking
└── reviews/{persona_id}/                       # All outputs for this persona
    ├── campaign_review.md                      # From persona_review_node
    ├── validation_report.md                    # From validation_node
    └── final_campaign.md                       # From finalizer_node
```

**Example**:
```
s3://ea-campaigns/campaigns/camp_20260204_001/
├── brief.md
├── status.json
└── reviews/persona_023/
    ├── campaign_review.md
    ├── validation_report.md
    └── final_campaign.md
```

## Key Insights

### ✅ What Works Well

1. **LangGraph State**: Explicit, type-safe, easy to debug
2. **Persona Store**: Simple, thread-safe, works for single execution
3. **S3 Persistence**: All results saved, no data loss
4. **Sequential Flow**: Clear order of operations

### 🔄 What Could Be Improved (Optional)

1. **Move persona_id to State**: Eliminate global store
   ```python
   state["persona_id"] = "persona_023"  # Instead of global
   ```

2. **Add Checkpointing**: Resume if Lambda times out
   ```python
   workflow.compile(checkpointer=MemorySaver())
   ```

3. **Add AgentCore Memory**: Learn from past campaigns
   ```python
   memory.retrieve(query=campaign_content)
   ```

### ❌ What's NOT Needed

1. **AgentCore Memory**: Not used, not needed for current use case
2. **Memory Hooks**: Not used, not needed
3. **Cross-invocation Memory**: Each campaign is independent

## Conclusion

The LangGraph implementation correctly handles memory through:
- **Explicit state management** (better than Strands)
- **Simple persona store** (preserved from original)
- **S3 persistence** (unchanged)

No memory functionality was lost in the conversion. In fact, state management is now more transparent and easier to debug.

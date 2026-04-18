---
inclusion: manual
---

# Clarification Questions Template

## Purpose

This template documents information gaps that are architecturally significant but not present in source documents. Use it during Requirements Generation to capture questions, default assumptions, and resolution status. Answering these questions improves architecture quality; each question includes a default assumption used if left unanswered.

## Template Structure

```markdown
# Clarification Questions

**Project**: [Project name]
**Stage**: [Stage number and name — e.g., 2 — Requirements Generation]
**Purpose**: These questions identify information gaps that are architecturally significant but not present in the source documents. Answering them will improve the quality of the architecture design. Each question includes a default assumption that will be used if you choose not to answer.

---

## CQ-001: [Short Title]

**Priority**: Critical | Important | Nice to Have
**Status**: Open | Resolved

**Question**: [Specific, actionable question for the stakeholder]
**Why it matters**: [How the answer changes the architecture — describe both paths]
**Default assumption if not answered**: [Specific assumption the architecture stage will use — be concrete]
**Source gap**: [Which source document was checked and what was missing]

---

## CQ-002: [Short Title]

**Priority**: Critical | Important | Nice to Have
**Status**: Open | Resolved

**Question**: [Specific, actionable question for the stakeholder]
**Why it matters**: [How the answer changes the architecture — describe both paths]
**Default assumption if not answered**: [Specific assumption the architecture stage will use — be concrete]
**Source gap**: [Which source document was checked and what was missing]

---
```

## Priority Definitions

- **Critical** — blocks a key architecture decision; the default assumption carries significant risk if wrong
- **Important** — influences design choices; the default assumption is reasonable but may require rework
- **Nice to Have** — minor impact; the default assumption is safe for most scenarios

## Status Values

- **Open** — awaiting stakeholder input; default assumption will be used if not answered before architecture stage
- **Resolved** — stakeholder provided an answer; record the answer inline and promote to a requirement with source citation `"User-provided answer (Task 2.3)"`

## Resolved Question Format

When a question is answered, update the entry:

```markdown
## CQ-001: [Short Title]

**Priority**: Critical
**Status**: Resolved
**Answer**: [Stakeholder's answer verbatim or paraphrased]

**Question**: [Original question]
**Why it matters**: [Original rationale]
**Default assumption if not answered**: [Original default — kept for audit trail]
**Source gap**: [Original source gap]
```



---

### 2. `docs/decisions.md`

Put this in:

```markdown
# Architectural Decisions

## Decision 001 — Keep the AI Model Replaceable

**Date:** August 30, 2026

**Decision:**

Butler will not be permanently tied to a particular AI model or provider.

**Reason:**

Butler's identity, memory, permissions, tools, and decision-making architecture should belong to Butler itself.

The underlying AI model should be replaceable as Butler develops.

---

## Decision 002 — Separate Conversation from the Brain

**Date:** August 30, 2026

**Decision:**

Conversation history is managed by a dedicated Conversation component rather than being stored directly inside the Brain.

**Reason:**

The Brain is responsible for intelligence and response generation.

Conversation is a separate concern and may eventually become part of a larger memory architecture.

---

## Decision 003 — Build Before Training

**Date:** August 30, 2026

**Decision:**

Butler will initially use existing AI capabilities rather than training a foundation model from scratch.

**Reason:**

We need to discover Butler's actual requirements, behavior, architecture, and data needs before considering custom model training.
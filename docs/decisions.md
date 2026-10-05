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

---

## Decision 004 — Separate Evidence from Verification Results

**Date:** October 4, 2026

**Decision:** Preserve received evidence separately from a claim's evaluation. Provenance describes origin; verification describes the judgment and its evidentiary basis. Future fact-checking and threat/deception detection share this foundation while retaining distinct responsibilities from Gatekeeper, retrieval, and reasoning.

**Reason:** Incoming information must not declare itself true. Evidence & Verification Foundation v0.1 establishes these models without prematurely adding automatic research, detection, or a new database.

---

## Decision 005 — Preserve History and Rank Current Relevant Memories

**Date:** October 4, 2026

**Decision:** Keep inactive memories in storage, exclude them from normal relevant-memory retrieval, and rank active matches by relevance before provenance and confidence. Weight content/category/value/subject matches 1/2/2/3 and isolate relevance scoring in `_score_memory_relevance()`.

**Reason:** Obsolete information should not supply current answers; strong provenance should not elevate irrelevant information. Structured subjects should matter more than incidental mentions. Improved Retrieval v1A is the initial explicit policy; conceptual matching is the next target in v1B.

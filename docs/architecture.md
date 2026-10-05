# Butler Architecture

## Current Architecture

Butler is currently organized into separate components with distinct responsibilities.

```text
                    BUTLER
                       |
          +------------+------------+
          |                         |
        Brain                  Conversation
          |                         |
    Response logic           Current dialogue
          |
      Identity
          |
       Config

```

## Responsibility Boundaries — October 4, 2026

- **Gatekeeper:** the intended boundary for incoming information, permissions, and appropriate actions. Currently only standalone message storage and local `.eml` import exist; live inbox access, classification, and action policy are deferred.
- **Provenance:** records where information came from. Source identity alone does not establish truth.
- **Evidence/Verification:** distinguishes received information from an evaluation of a claim and the reasons for trusting or disputing it.
- **Retrieval:** selects relevant, currently usable information. Relevance and evidentiary strength are separate dimensions.
- **Reasoning:** will determine which conclusions and answers/actions the available information can responsibly support. Brain currently uses simple response rules and returns the highest-ranked matching memory; general reasoning is future work.

The conceptual direction is `Question/Input → Gatekeeper → Retrieval → Evidence/Provenance → Verification → Reasoning → Answer/Action`. This is an architectural guide, not an implemented end-to-end pipeline.

Future fact-checking and threat/deception detection (including spam and phishing) should be sibling consumers of the same evidence and verification foundation. An email claiming an account is suspended establishes that someone made the claim; it does not establish that the account is suspended. Automatic web research, source-quality scoring, detection, and verification-result persistence remain deferred.

## Evidence & Verification Foundation v0.1

`Evidence` and `VerificationResult` are separate concepts in `verification/evidence.py`.
Evidence records `claim`, `content`, `source_type`, `verification_status`, and optional `confidence`. It starts `unverified`; permitted states are `unverified`, `supported`, `disputed`, and `unknown`. Evidence is not automatically truth.

VerificationResult separately records an evaluated claim, `supported`/`disputed`/`unknown` status, `low`/`medium`/`high` confidence, a reason, and the evidence behind the judgment. It validates status and confidence and owns its evidence list. These are data models, not an automatic verification engine.

## Improved Retrieval v1A

`PersonalMemoryStore.find_relevant_memories()` searches `content`, `category`, `value`, and `subject`. Only memories with `status="active"` and a positive relevance score are returned. Inactive memories remain stored: storage preserves history while retrieval determines what is currently usable. This filter applies to relevant-memory retrieval; `get_memories()` and the explicit recall-all response still expose stored history.

`_score_memory_relevance()` isolates the weighted word-overlap calculation:

| Field | Weight per shared query word |
| --- | --- |
| content | 1 |
| category | 2 |
| value | 2 |
| subject | 3 |

Query words are lowercased, stripped of `.,?!`, and retained only when longer than three characters. Matches use word sets, so repetitions within a field do not increase its score. A structured `subject="coffee"` can match “What coffee do I like?” even when the content is “Sumatra is my usual choice.”

Ranking is descending by **relevance, then provenance, then confidence**. Source strengths are `direct_user_statement=3`, `inference=1`; confidence strengths are `high=3`, `medium=2`, `low=1`. Missing or unrecognized values receive 0. Provenance cannot make an irrelevant memory relevant. The weights are an initial testable policy, not a calibrated truth measure.

Retrieval still requires literal word overlap in at least one searched field. **Improved Retrieval v1B** will address conceptual relevance when a question and memory use different words, such as “What do I like to drink?” versus a coffee preference; the implementation approach remains open.

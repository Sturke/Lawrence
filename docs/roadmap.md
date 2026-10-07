# Butler Roadmap

## Foundation

- [x] Project structure
- [x] Configuration
- [x] Butler startup
- [x] Basic interaction loop
- [x] Brain component
- [x] Conversation component
- [x] Automated testing
- [x] Git version control
- [x] Architecture documentation

## Memory

- [x] Persistent personal memory storage (SQLite)
- [x] Structured personal memory, updates, and legacy migration
- [x] Provenance v1A
- [x] Memory retrieval — Improved Retrieval v1A (structured fields, active filtering, provenance/confidence ranking, weighted relevance, scoring helper)
- [ ] Memory relevance — Improved Retrieval v1B: conceptual relevance beyond literal word overlap (**next target**)
- [ ] Memory rules — broader policy beyond current active-status filtering
- [ ] User-controlled memory — extend existing explicit `remember:` support

## Intelligence

- [ ] AI model integration
- [ ] System instructions
- [ ] Context management
- [ ] Reasoning and planning
- [ ] Model abstraction

## Tools

- [ ] Tool architecture
- [ ] Tool permissions
- [ ] Tool execution
- [ ] Tool results

## Trust and Safety

- [x] Gatekeeper message persistence and local saved-email import
- [x] Evidence & Verification Foundation v0.1 — separate Evidence and VerificationResult models
- [ ] Fact-checking using the shared evidence/verification foundation
- [ ] Threat/deception detection using that foundation (spam/phishing included)

- [ ] Permission system
- [ ] Confirmation for consequential actions
- [ ] Privacy boundaries
- [ ] Audit/history
- [ ] Error handling

## Future

- [ ] Learning from feedback
- [ ] Butler-specific datasets
- [ ] Fine-tuning evaluation
- [ ] Determine whether custom model training is justified

## Current Checkpoint — October 4, 2026

**51 passing tests**, `f4f399c` — `Improve structured memory retrieval`.
Evidence & Verification Foundation v0.1 was completed in `05b6778` —
`Add evidence and verification foundation`; Improved Retrieval v1A followed.
The development checkpoint was committed and pushed, with `main` synchronized
with `origin/main` and the working tree clean before this documentation pass.

Next: **Improved Retrieval v1B**, followed by further retrieval/reasoning work.
Automatic verification, web research, source-quality scoring, and threat detection
remain future capabilities rather than completed features.

## Established Review and Offshoot Items

- [ ] **Meta Muse Architecture Review checkpoint** — a design-validation review of Gatekeeper/control-layer separation, structured memory, permissions and approval, audit/provenance, tool use and creation, background autonomy, multi-agent coordination, prompt-injection defenses, execution environments, connectors, and model independence. Compare published architecture with Lawrence’s independent design; verify external product claims during the review. This is a review checkpoint, not a separate build project.
- [ ] **Bench Power Supply** — a supporting electronics learning project using Burke’s saved computer PSU. The “Building Bench Power Supply” discussion identifies the donor as a Cooler Master 550 W supply and proposes a protected fixed-voltage build before considering adjustable outputs. The intended learning includes power requirements, wiring, connectors, measurement, protection, and circuit debugging, with a reusable supply for later Lawrence hardware experiments. Design work stays on the low-voltage output side with the PSU enclosure intact. The build remains planned; completion is not recorded.
- [ ] **Dactyl Manuform Keyboard** — a supporting learning project combining fabrication, soldering, hand-wiring, microcontrollers, firmware/keymaps, testing, and human-interface design. Layout, components, and fabrication choices remain open. The project develops practical skills for Lawrence hardware work; completion is not recorded.
- [ ] **Robot Mower/Rover and smart-home projects** — related hardware offshoots referenced in the power-supply and keyboard discussions. Retain these items without assigning new scope or dates.

The hardware projects support Burke’s learning while building Lawrence; they do not replace Improved Retrieval v1B as the next assistant-development target.

## Relationship to the Lawrence Master Documents

This repository roadmap is the **implementation roadmap for the Butler codebase**.
It records what has been implemented, validated, and identified as the next
software-development target.

The broader Lawrence program is maintained in three companion master documents:

- **LAWRENCE_BUTLER_ROADMAP.md** — the master strategic roadmap for Project Butler
  and the path toward Lawrence.
- **LAWRENCE_DESIGN_CHARTER.md** — the working design authority for user sovereignty,
  privacy, memory, permissions, auditability, safety boundaries, and related
  architectural requirements.
- **LAWRENCE_VALIDATION_REGISTER.md** — the companion validation framework for
  testing whether Lawrence satisfies the Charter and other accepted requirements.

The **Lawrence Design Charter v0.1 working draft exists**. Its requirements and
authority model are not yet fully accepted or enforced in code. Future work
includes reviewing applicable Charter rules with Burke, versioning accepted
requirements, making appropriate rules machine-readable, and connecting them
to Gatekeeper enforcement.

The **Lawrence Validation Register v0.1 exists as a scenario draft**. Its T01–T12
validation scenarios have not yet been run. Future work includes refining these
into executable validation tests, recording evidence and results, and maintaining
the register as Lawrence gains capabilities.

The master roadmap also defines **Documentation, Introspection & Self-Review** as
a future Lawrence capability. After sufficient retrieval, reasoning, Gatekeeper,
and tool foundations exist, Lawrence should first gain read-only ability to
inspect his own repository and authoritative project documents, compare
implementation and tests against documented claims, identify documentation
drift, and propose evidence-backed updates. Applying documentation changes is a
later bounded action requiring appropriate authorization. Self-documentation
does not imply autonomous self-modification.

Detailed long-range architecture, autonomy stages, Butler Body development,
supporting learning projects, and other future capabilities belong in the master
roadmap rather than being duplicated in this repository implementation roadmap.

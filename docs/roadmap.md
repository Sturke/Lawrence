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

- [ ] Meta Muse Architecture Review checkpoint
- [ ] Related offshoot projects

These previously established items remain on the roadmap. Their detailed scope,
dependencies, and timing are not recorded in the current repository or the
referenced conversation; this update does not assign or change them. The Design
Charter and Validation Register remain established documentation references;
their contents are not present here and have not been reconstructed.

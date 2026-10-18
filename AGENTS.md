# Codex instructions for Butler / Lawrence

Before changing this repository, read [the accountability protocol](docs/accountability.md)
and [current project status](docs/project_status.md). Follow the startup checkpoint,
work within one objective, and leave a verified session handoff.

Read README.md, docs/roadmap.md, docs/decisions.md, and the architecture/component
docs relevant to the task. Inspect Git status and applicable nested instructions;
preserve existing user changes. If records conflict, report the conflict and use
current code/tests as evidence of behavior; do not silently rewrite accepted intent.

The roadmap owns milestones; decisions.md owns accepted architectural decisions;
project_status.md owns the current checkpoint. Link to these rather than copying
their contents. Conversation and assistant memory are context, not project authority.

Preserve model independence, Brain/Conversation separation, evidence/result
separation, and existing retrieval policy unless the user authorizes a change.
Do not broaden the objective into future Lawrence capabilities or hardware work.
Label proposals and assumptions explicitly; do not mark milestones complete without
supporting evidence. Add a decision record only for a newly accepted architectural
choice, not routine session notes.

Run checks appropriate to the change. The full regression command is
`.venv/bin/python -m pytest -q` from the repository root. Record the actual result,
including failures or checks not run. Never reuse an old test count as verification.
Review and show the final diff (including new files), update project_status.md,
and report remaining work. Do not commit or push without explicit user approval.

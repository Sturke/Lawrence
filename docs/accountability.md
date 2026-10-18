# Project Accountability Protocol

This is our shared working agreement for Burke and Codex. Keep it lightweight:
one current status record, one session objective, and evidence for completion.
It is a development workflow, not an implemented Lawrence runtime capability.

## Session startup checkpoint

Before editing, Codex reads AGENTS.md, project_status.md, the roadmap, decisions,
and relevant implementation docs, then checks the branch, HEAD, working tree,
and relevant code/tests. Preserve existing changes and identify stale or conflicting
claims. Burke supplies corrections or changed priorities; Codex makes discrepancies
visible instead of asking Burke to reconstruct the project history.

State a short checkpoint in chat: observed starting state, **one objective**, a
concrete completion condition, and the checks planned. Use the user's request as
authorization for that objective; ask only when an unresolved ambiguity or scope
change actually needs Burke's decision. Baseline tests are useful when establishing
status or investigating behavior; do not run them mechanically for every discussion.

## Evidence and assumptions

Separate observed facts (file/commit references and actual check results), historical
reports (dated prior claims), assumptions, and proposed work. Code shows what exists;
tests show only the behavior exercised. Passing tests do not prove all requirements
or manual workflows. A roadmap checkbox records intent/status and is not test evidence.
When evidence and documentation disagree, record the discrepancy and its limits.
Do not infer completion from conversation, a remembered test count, or a draft plan.

Repository implementation milestones belong in [roadmap.md](roadmap.md); accepted
architectural choices belong in [decisions.md](decisions.md). Broader master-document
relationships and draft validation status are defined by the roadmap. If those
external documents are unavailable, say so instead of inventing their contents.

## One objective and scope control

Define done before expanding the work. Complete the smallest coherent increment
that meets it and protects established behavior. Park unrelated discoveries in the
status handoff with a short reason; do not turn them into new commitments, dates,
or completed milestones. Propose a scope change and obtain Burke's agreement before
pursuing it. Stop reopening settled decisions unless new evidence or Burke's request
justifies review; reference the existing decision and explain what changed.

## Verification

Run checks proportional to the change and any repository-required checks. For code,
exercise the changed behavior and relevant regressions; use the full suite when
establishing the project baseline. For documentation, check links, consistency,
whitespace, and the complete diff. Record date, HEAD, command, result, and limitations
in project_status.md. Distinguish automated tests, manual observations, and unrun
validation scenarios. Report failures and blockers honestly; never relabel an unrun
check as passed or silently mark unfinished work complete.

## Session handoff

Before ending, review Git status and all diffs, including new files. Update the
single current checkpoint in [project_status.md](project_status.md) with:

- Objective and outcome: completed, partial, or blocked, with evidence.
- Branch/base HEAD and changed files; whether changes are uncommitted.
- Checks actually run and results; checks not run and remaining uncertainty.
- Blockers, parked work, and one concrete next action (label proposals).

Keep historical detail in Git rather than appending a transcript. Update milestone
checkboxes only when the completion condition is met. Add decisions only when an
architectural choice has been accepted. Show the diff and summarize the outcome to
Burke. Commit and push require explicit approval; completion of editing is not approval.

## Limits of conversational memory

Conversation and assistant memory can suggest where to look but cannot replace these
records. Codex must re-read the current repository each session; if access is missing,
request the current records and label any answer based on older context. AGENTS.md
helps assistants that load repository instructions; it cannot enforce behavior in
unconnected ChatGPT chats or guarantee compliance. Neither participant should assume
that an earlier conversation, decision, or test result was retained accurately.

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

## Branches and approval

Follow [Decision 007](decisions.md#decision-007--controlled-ai-assisted-development-workflow).
Retain both checkouts. Use the ChatGPT checkout for feature branch work
and verify its base against GitHub's `main` before starting. Burke delegates
implementation, testing, documentation, feature-branch commits and pushes,
and pull request preparation within the agreed scope.

Before pushing, inspect every changed and staged file, including additions.
Keep real emails, personal data, credentials, and local databases outside
version control. Use synthetic fixtures and keep CI independent of personal
accounts and sample collections.

Open a pull request against `main`, with scope, verification, and known
limitations in its description. `main` requires a pull request and the
GitHub Actions **Python tests** check. Disable force pushes and deletion,
and apply protection to administrators. Record the controls actually
verified on GitHub. Burke's explicit approval to merge is a separate
decision for the reviewed pull request head. When Burke's account authors
the pull request, record the approval in chat or as a PR comment. GitHub's
formal review approval requires a different account from the PR author.

## Pull request review checklist

1. **Read the summary.** Open the PR link from the handoff. On GitHub's
   **Conversation** tab, check that the base is `main`, the work matches
   what you asked for, and the summary explains the remaining limitations.
2. **Review the changes.** Open **Files changed**. Start with the decision,
   user-facing docs, or tests that describe the behavior you asked for.
   Look for unexpected changes to scope, personal data access, permissions,
   or automatic actions. Ask in chat or comment on the file if anything
   needs explanation or revision.
3. **Check the results.** Open **Checks** and confirm **Python tests** passed
   for the latest commit. If checks are pending or failing, Codex will report
   the result and address any failure within scope before handing it back.
4. **Decide whether to merge.** If changes are needed, tell Codex what to revise
   and review the updated PR after CI reruns. If the PR is ready, either merge
   it yourself on GitHub or explicitly authorize Codex. For example, write
   “I reviewed PR #N at commit SHA and authorize you to merge it into main.”
   When your account authored the PR, use chat or a **Conversation** comment
   to record approval. If the reviewed changes are revised, review and approve
   the new version before merging.
5. **Confirm the new baseline.** After merging, Codex verifies GitHub's
   `main` and updates the Lawrence checkout with a fast-forward. The original
   Butler checkout can be updated when needed. Start the next feature from
   the new approved baseline.

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
Burke. Report the feature branch, commit or pull request link, CI status,
and any unverified protection settings. Leave the pull request open for
Burke's merge decision.

## Limits of conversational memory

Conversation and assistant memory can suggest where to look but cannot replace these
records. Codex must re-read the current repository each session; if access is missing,
request the current records and label any answer based on older context. AGENTS.md
helps assistants that load repository instructions; it cannot enforce behavior in
unconnected ChatGPT chats or guarantee compliance. Neither participant should assume
that an earlier conversation, decision, or test result was retained accurately.

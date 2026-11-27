# Current Project Status

## Manual saved-email quarantine

- Added a local command to move one explicitly selected saved email into
  quarantine, list quarantined filenames, and restore a file to an existing
  folder. Review findings stay advisory. Mailbox access and automatic routing
  remain future work.
- Move and restore preserve the original bytes, refuse filename collisions
  and symlink inputs, and require a common filesystem. The original file
  remains in place if the destination cannot be created.
- Lawrence now has its own local virtual environment. The full suite passed
  115 tests with `.venv/bin/python -m pytest -q -p no:cacheprovider`.
  `git diff --check` passed. Quarantine verification used synthetic local files,
  and the interactive review session opened from the Lawrence checkout.

## Authenticated tracking-link exceptions

- Added an opt-in exception for a sender domain, visible hostname, and tracking
  hostname supplied together. It requires exact From-domain DKIM authentication.
  Successful exceptions remain visible in JSON and text, and other findings
  still count toward Review.
- The CLI regression initially failed because the option was unavailable.
  Simulated cases cover the approved combination, different tracking and visible
  hosts, failed or mismatched authentication, and a separate credential finding.
  The full suite passed 113 tests using the original checkout's virtual
  environment with `python -m pytest -q -p no:cacheprovider`.
  `git diff --check` passed.
- Gatekeeper verified live DKIM for the saved Holiday Happenings newsletter
  and authenticated `cuhumane.org`. The exact sender and tracking-host
  combination remains unapproved, so the link mismatch still triggers Review.

## Visible URL hostname comparison

- Extended the saved-email link check to compare a bare domain or a full
  HTTP(S) URL label with the destination hostname. The new test first failed
  because full URLs were skipped. It now covers different hostnames, the same
  hostname with different URL components, and malformed or prose labels.
- The full suite passed 112 tests using the original checkout's virtual
  environment with `python -m pytest -q -p no:cacheprovider`.
  `git diff --check` passed.
- The offline rerun imported all 19 labeled messages and sent 4 of 9 suspicious
  emails and 2 of 10 legitimate emails to Review. The newly flagged samples
  were the Compass Mining verification email and the legitimate Holiday
  Happenings newsletter. No links were opened.
- The authenticated tracking-link exception above provides an opt-in way to
  reduce this false positive after confirming the exact tracking host.

## Action-link coverage investigation — November 26, 2026

- Started from clean `main` at `6063523`. The labeled validation batch
  sent 3 of 9 suspicious messages and 1 of 10 legitimate messages to Review.
- Four of the six misses contained web action links. Three used cloud-hosted
  HTML pages. One had a verification button and a displayed full URL whose
  actual destination was a different host. The two invoice and ledger
  samples had no HTTP(S) action link in their parsed bodies.
- Added one saved-email CLI characterization test with six fictional cases
  and a domain-only label as a positive control. The test documents current
  coverage. It adds no detection rules. The full suite passed 112 tests
  with the original checkout’s virtual environment using
  `python -m pytest -q -p no:cacheprovider`. `git diff --check` passed.
- The test and this status update are uncommitted. Proposed next step:
  compare the hostname in visible HTTP(S) URL labels with the actual
  destination, using matched and mismatched pairs plus legitimate tracking
  examples. No links were opened.

## Prior checkpoint — November 26, 2026

- Local `main` includes `609b179` (`Add Gatekeeper brand and action-link
  screening`), one commit ahead of `origin/main` as of November 26.
  It includes the saved-email rules below and the opt-in brand check for
  unexpected sender domains on supported sensitive subjects. See the
  [assessment guide](gatekeeper-assessment.md) for the rules and CLI usage.
- The CLI regression initially failed because the option was unavailable.
  The final suite passed 111 tests using `python -m pytest -q -p no:cacheprovider`
  with the original checkout's virtual environment. `git diff --check` passed.
  Verification used fictional brand and sender data, including a lookalike
  domain, approved mail provider, and newsletter.
- Next: validate the rules on a fresh, labeled batch of legitimate and
  suspicious saved emails. Use independently verified sender domains for
  any real brands included in that check. Live inbox access, permission
  enforcement for mailbox actions, and autonomous routing remain future work.

## Saved-email validation — November 25, 2026

- Started from clean `main` at `6ccf196`. Offline baseline: 18 saved
  messages imported, three flagged. The user labeled six samples as scams
  or phishing, and one of those six triggered review at baseline.
- Added low-confidence findings for urgent external action links,
  urgent cloud-hosted payment pages with no usable From address, and
  cloud-hosted home warranty quote pages outside the claimed From domain.
- The final offline rerun imported all 18 messages and flagged seven.
  Five of the six labeled samples triggered review, with the Black Friday
  promotion still inconclusive. The dispositions for the other 12 stayed
  the same.
- The first synthetic regression failed before its rule was added. The final
  suite passed 110 tests using `python -m pytest -q -p no:cacheprovider` with
  the original checkout's virtual environment. The batch text report also
  completed successfully. `git diff --check` passed. Batch runs used
  temporary databases and opened no links.
- These samples informed rule design. Use a separate set to measure how
  the rules generalize.

## Multipart body screening — November 25, 2026

- Completed the multipart body screening increment in the writable Lawrence
  checkout. Clean starting point: `main` at `9b6cb80`, which records the
  interactive review verification previously listed as pending below.
- Gatekeeper now checks extracted HTML for credential and payment phrases
  even when plain text is present. It records one finding per category,
  preferring subject evidence and then plain-text evidence when either matches.
- The multipart screening change was committed and pushed as `6ccf196`
  (`Screen both email body formats in Gatekeeper`).
- On November 25, the original virtual environment's Python ran
  `-m pytest -q -p no:cacheprovider` in the working copy. The baseline passed
  107 tests. The new regression first failed because HTML screening was
  skipped for multipart mail. After implementation, all 108 tests passed.
  `git diff --check` passed. The new case used a synthetic saved email.

## Verified checkpoint — November 14, 2026

- Completed milestone — Improved Retrieval v1B was committed as `44ec2a1`
  (`Complete bounded Improved Retrieval v1B`). At startup, `main` matched the
  local `origin/main` reference and the working tree was clean.
- Completed milestone — [Gatekeeper Email Assessment v0.1](gatekeeper-assessment.md) was committed as `8718014` and pushed to GitHub’s `main` branch.
  The local implementation is verified and reviewed. The opt-in importer
  assesses plain-text email and emits JSON with the stored message ID,
  low-confidence findings, source excerpts, and coverage limits. A message
  with no matching phrases is inconclusive.
- Completed milestone — [Gatekeeper Email Assessment v0.2](gatekeeper-assessment.md)
  was committed as `4358273` and pushed to GitHub’s `main` branch.
  It flags differences between the `From` and `Reply-To` domains as
  low-confidence findings. The JSON record reports version `0.2`.
  All 79 tests passed in Warp, including the domain mismatch and
  case-insensitive match tests. `git diff --check` passed.
- Completed milestone — [Gatekeeper Email Assessment v0.3](gatekeeper-assessment.md)
  was committed as `c65d453` and pushed to GitHub’s `main` branch.
  It flags differences between a domain shown in an HTML link label and
  the HTTP or HTTPS destination hostname, recording both as unverified
  evidence in a low-confidence finding. All 81 tests passed in Warp,
  including the matching and mismatched link cases.
- Files in this checkpoint: `tools/gatekeeper_import.py`, `verification/email_assessment.py`,
  `tests/test_gatekeeper_assessment.py`, and the assessment, import, architecture,
  roadmap, and project status documents.

## Verification

- Warp access was blocked by the computer-use tool. Shell `git status` and
  `git log -1 --oneline` confirmed the startup checkpoint.
- System `python3 -m pytest -q` could not run because pytest was absent.
  A local virtual environment using Homebrew Python ran the existing suite
  before implementation (75 passed). Both new acceptance tests then failed
  because `--assess` was unsupported.
- Final `.venv/bin/python -m pytest -q` with the pinned pytest 9.1.1: 77 passed.
  Burke independently confirmed 77 passing tests in Warp after activating
  Butler’s virtual environment. Tests use temporary SQLite stores. `git diff --check` passed.
- Manual verification in Warp — A Gmail export and an Apple Mail export both imported successfully as local `.eml` files. Both assessments returned
  `inconclusive` with no matching phrases. The automated acceptance tests
  cover the `review_required` outcome.
- Broader detection, sender authentication, inbox access, and autonomous action
  remain outside this increment. Master-document scenarios were not validated.

## Current handoff — November 15, 2026

- Completed milestone — [Gatekeeper Email Assessment v0.4](gatekeeper-assessment.md)
  was committed as `8c2caa2` and pushed to GitHub’s `main` branch. It
  reports whether the header and HTML link domain checks could compare inputs.
  A matching HTML link now reports one comparison and zero findings.
- Started from clean `main` at `f7e66f1`, aligned with local `origin/main`.
  At closeout, `main` and `origin/main` pointed to `8c2caa2`.
- The new assertion failed against v0.3 because the JSON had no `checks` field.
  After implementation, `.venv/bin/python -m pytest -q` passed all 82 tests,
  including missing HTML, HTML with zero eligible links, and matching and
  mismatched links. `git diff --check` passed.
- Manual v0.4 verification in Warp: the Gmail and Apple Mail exports both
  returned `inconclusive` with no findings. The Gmail export had matching
  `From` and `Reply-To` domains. The Apple Mail export skipped that check
  because at least one usable header domain was unavailable. Both HTML
  bodies yielded zero eligible links.
- The manual test guide and status update were committed as `16cb190`.
- Completed milestone — [Gatekeeper Email Assessment v0.5](gatekeeper-assessment.md)
  was committed as `401f5e4` and pushed to GitHub’s `main` branch. It
  recognizes supported account sign-in notice subjects and quotes the subject
  as unverified evidence in `recognized`. Risk findings determine disposition.
- Started from clean `main` at `16cb190`, aligned with `origin/main`.
  At closeout, `main` and `origin/main` pointed to `401f5e4`.
- Both new acceptance tests initially failed because `recognized` was missing.
  After implementation, `.venv/bin/python -m pytest -q` passed all 84 tests.
  `git diff --check` passed.
- Manual v0.5 verification in Warp: the saved Apple Mail export returned
  `account_sign_in_notice` with an unverified subject excerpt. The risk
  disposition was `inconclusive` with no findings.
- The v0.5 checkpoint was closed in `3443ccd`.
- Completed milestone — [Gatekeeper Email Assessment v0.6](gatekeeper-assessment.md)
  was committed as `fa9f50c` and pushed to GitHub’s `main` branch. It extracts
  `service` and an optional `sign_in_method` from supported sign-in notice subjects. The quoted subject
  remains unverified evidence, and risk findings still determine disposition.
- Started from clean `main` at `3443ccd`, aligned with `origin/main`.
  At closeout, `main` and `origin/main` pointed to `fa9f50c`.
- Three focused tests failed against v0.5 because `details` was missing.
  After implementation, `.venv/bin/python -m pytest -q` passed all 85 tests.
  `git diff --check` passed.
- Manual v0.6 verification in Warp: the saved Apple Mail export returned
  `account_sign_in_notice` with service `iCloud` and method `a web browser`.
  The subject evidence remained unverified, and the risk disposition was
  `inconclusive` with no findings.
- The v0.6 checkpoint was closed in `130bd3e`.
- Completed milestone — [Gatekeeper Email Assessment v0.7](gatekeeper-assessment.md)
  was committed as `b5fab4f` and pushed to GitHub’s `main` branch.
  It recognizes supported password reset subjects and quotes the subject as
  unverified evidence. Risk findings determine disposition.
- Started from clean `main` at `130bd3e`, aligned with `origin/main`.
  At closeout, `main` and `origin/main` pointed to `b5fab4f`.
- Two positive recognition tests initially failed against v0.6, while the
  routine password email was correctly left unlabeled. After implementation
  `.venv/bin/python -m pytest -q` passed all 88 tests and `git diff --check`
  passed. Tests use synthetic saved emails.
- The v0.7 checkpoint was closed in `7e364f0`.
- Completed milestone — Gatekeeper v0.8 was committed as `3229371` and
  pushed to `main`. It recognizes supported password change
  subjects separately from password reset requests and quotes the subject
  as unverified evidence.
- Started from clean `main` at `7e364f0`, aligned with `origin/main`.
- The new saved-email test initially failed because v0.7 had no recognition
  for password changes. After implementation, `.venv/bin/python -m pytest -q`
  passed all 89 tests and `git diff --check` passed. Verification used a
  synthetic saved email.
- Completed milestone — Gatekeeper v0.9 was committed as `7947f81` and
  pushed to `main`. It reports an exact match against
  user-supplied approved addresses. Sender trust stays unverified pending a
  reliable source of authentication evidence.
- Started from clean `main` at `3229371`, aligned with `origin/main`.
  At closeout, `main` and `origin/main` pointed to `7947f81`.
- The new saved-email test failed against v0.8 because the approval option
  was absent. After implementation, all 90 tests passed with
  `.venv/bin/python -m pytest -q`. The test covers exact and same-domain
  non-matches, unverified status despite a claimed authentication pass, and
  preservation of the risk verdict. `git diff --check` passed.
- Manual v0.9 verification in Warp: the saved Apple export matched the
  address only when supplied with `--approved-sender`. Both runs reported
  the sender as unverified.
- The v0.9 checkpoint was closed in `d0c933e`.
- Completed milestone — Gatekeeper v0.10 was committed as `db25c1e` and
  pushed to `main`. It stores explicit sender approvals in SQLite and supports
  approving, listing, and removing addresses.
- Started from clean `main` at `d0c933e`. At closeout, `main` and
  `origin/main` pointed to `db25c1e`.
- The new test initially failed because the sender command was absent.
  After implementation, `.venv/bin/python -m pytest -q` passed all 91 tests.
  The test confirms persistence across imports, removal, and unverified
  status for an approved address. `git diff --check` passed.
- Manual v0.10 verification in Warp: the saved Apple export matched its
  SQLite approval without a per-run option. Sender status was `unverified`
  and risk disposition was `inconclusive`.
- Completed milestone — Gatekeeper v0.11 was committed as `c5d5ddb` and
  pushed to `main`. It adds opt-in DKIM verification against DNS keys,
  with exact From-domain matching and full-body signatures.
- Started at `db25c1e` on `main`, with the v0.10 status closeout already
  pending. The v0.11 commit includes that closeout.
- Standalone Warp probe verified a signature on the saved Apple export
  with signing domain and From domain both `email.apple.com`.
- The CLI test first failed because `--verify-dkim` was absent. After
  implementation, `.venv/bin/python -m pytest -q` passed all 92 tests using
  a stub verifier for the integration test. `git diff --check` passed.
- Manual v0.11 verification in Warp: the integrated CLI authenticated
  `email.apple.com` via DKIM for the saved Apple export. The per-run approved
  address matched, mailbox identity stayed unverified, and the risk verdict
  was inconclusive with no findings.
- The v0.11 checkpoint was closed in `d2ed5df`.
- Completed milestone — The opt-in text report was committed as `ee0817e`
  and pushed to `main`. It shows recognition, address approval, domain
  authentication, and risk separately.
- Started from clean `main` at `d2ed5df`. At closeout, `main` and
  `origin/main` pointed to `ee0817e`.
- The focused test initially failed because the format option was absent.
  After implementation, `.venv/bin/python -m pytest -q -p no:cacheprovider`
  passed all 93 tests. `git diff --check` passed.
- Manual verification in Warp: the text report recognized the iCloud sign-in
  notice, showed the approved address match, authenticated `email.apple.com`
  via DKIM, and reported inconclusive message risk on its own line.
- Saved-email 1.0 release checks passed in Warp: the Apple export reported
  an authenticated domain with DKIM enabled and an unverified domain with
  DKIM omitted, while the address approval matched in both runs. A synthetic
  credential request returned `review_required` and displayed its finding.
- Release baseline: clean `main` at `1462106`. The full test suite passed
  all 93 tests with `.venv/bin/python -m pytest -q -p no:cacheprovider`.
  The release validation notes were committed as `f56d6c5` and pushed.
- Completed milestone — [Gatekeeper Email Assessment 1.0](gatekeeper-assessment.md)
  was committed as `dd8352b` and pushed to GitHub’s `main` branch. The JSON
  assessment reports version `1.0`, and the guide documents the validated
  saved-email workflow and its limits.
- All 93 tests passed after the version update with
  `.venv/bin/python -m pytest -q -p no:cacheprovider`. At closeout, `main`
  and `origin/main` pointed to `dd8352b` and the working tree was clean
  before this documentation update.
- The 1.0 checkpoint was closed in `28d55e9`.
- Follow-up from real saved emails: the Bitwarden export authenticated
  its domain but its new-device sign-in subject was unrecognized. The
  TreasuryDirect export yielded two link mismatch findings whose domain
  pairs were visible in JSON only.
- The text report now prints the displayed domain and destination for each
  link mismatch. The new end-to-end test failed before the formatting change
  and passed after it. All 94 tests passed with
  `.venv/bin/python -m pytest -q -p no:cacheprovider`. Whitespace checks passed.
- The TreasuryDirect text rerun in Warp showed both domain pairs beneath
  the review verdict. The report change was pushed as `bb9160c`.
- New-device sign-in recognition now records the subject's stated platform
  as unverified evidence and displays it in the text report. Started from
  clean `main` at `bb9160c`. The assessment, formatter, test, and docs are
  uncommitted. The new test failed before implementation and all 95 tests
  passed afterward with `.venv/bin/python -m pytest -q -p no:cacheprovider`.
  `git diff --check` passed.
- Manual verification in Warp: the saved Bitwarden export was recognized as
  an account sign-in notice with reported platform `macOS`. DKIM authenticated
  `bitwarden.com` independently, and message risk was inconclusive.
- New-device sign-in recognition was pushed as `4a4ff03`.
- Real-email checks in Warp: the Jersey Mike’s and NPR reset notices were
  recognized and their domains authenticated via DKIM. The NPR password
  change notice authenticated via DKIM but its subject was unrecognized.
  Two other exports stopped at import because they lacked a plain-text body.
- Follow-up from clean `main` at `4a4ff03`: added recognition for “Your
  password has been updated”. The new regression test failed before the
  change. All 96 tests passed afterward with
  `.venv/bin/python -m pytest -q -p no:cacheprovider`. Whitespace check passed.
- Manual verification in Warp: the NPR export now reports a password change
  notice, authenticates `npr.org` via DKIM, and reports inconclusive risk.
- The NPR recognition change was pushed as `9cf9041`.
- HTML-only import started from clean `main` at `9cf9041`. It now assesses
  the subject and eligible HTML links, stores an empty plain-text body, and
  reports the skipped body phrase check. DKIM still uses the original bytes.
- The new HTML-only assessment test reproduced the import failure first.
  After the change, all 97 tests passed with
  `.venv/bin/python -m pytest -q -p no:cacheprovider`. Whitespace check passed.
- Manual verification in Warp: the HTML-only reset and Instagram password
  change exports both imported, authenticated their respective domains via
  DKIM, and reported skipped plain-text body checks. Both risk verdicts were
  inconclusive and neither subject was recognized.
- HTML-only import was pushed as `a375a4f`.
- Follow-up from clean `main` at `a375a4f`: recognize the confirmed subjects
  “Reset Password” and “Your Instagram password has been changed”. Both
  regression tests failed before implementation. Afterward all 99 tests
  passed with `.venv/bin/python -m pytest -q -p no:cacheprovider`, and
  `git diff --check` passed. The code, tests, and docs are uncommitted.
- Generalized the password-change recognition rule to accept one to five
  service words in “Your <service> password has been changed”. Tests cover
  another service and exclude help subjects. All 100 tests passed, and
  `git diff --check` passed.
- Manual verification in Warp: the two saved HTML-only originals now
  report password reset and password change respectively. Both domains
  authenticated via DKIM, risk was inconclusive, and both reports showed
  the skipped plain-text body check.
- The subject recognition update was pushed as `4568bd9`.
- Follow-up from clean `main` at `4568bd9`: assess phrases in extracted HTML
  text when the plain-text body is missing. The updated end-to-end test
  failed before implementation and verifies credential evidence, skipped
  script/style/head content, and continued link checks. All 100 tests passed
  with `.venv/bin/python -m pytest -q -p no:cacheprovider`. Whitespace check passed.
- Manual Warp reruns of the Stansberry and Instagram exports confirmed
  that extracted HTML text was checked. Both retained their expected notice
  labels and DKIM authentication, with inconclusive risk.
- HTML phrase coverage was pushed as `a8a84cc`.
- Follow-up from clean `main` at `a8a84cc`: the text report now shows the
  source and matched excerpt for phrase findings. Both focused tests failed
  before the change and passed after it. The full suite passed all 100
  tests with `.venv/bin/python -m pytest -q -p no:cacheprovider`.
  `git diff --check` passed. The phrase evidence display was pushed as
  `ea2cc06`.
- Follow-up from clean `main` at `ea2cc06`: the text report shows both
  domains beneath a Reply-To mismatch finding. The synthetic saved-email
  regression failed before the formatter update. Afterward, all 100 tests
  passed with `.venv/bin/python -m pytest -q -p no:cacheprovider`, and
  `git diff --check` passed. Reply-To evidence display was pushed as `01e702e`.
- Follow-up from clean `main` at `01e702e`: the text coverage line reports
  Reply-To match, mismatch, or skip and the HTML link count or skip reason.
  Both focused tests failed before the change. Afterward, all 101 tests
  passed with `.venv/bin/python -m pytest -q -p no:cacheprovider`, and
  `git diff --check` passed. The text coverage display was pushed as
  `0dd3e38` and verified on the TreasuryDirect export.
- Warp shell-loop batch baseline: 12 assessed, two required review, and
  zero import failures with DKIM off.
- From clean `main` at `0dd3e38`, added built-in folder assessment.
  The new test failed before the option existed and now verifies a
  recognized reset, an invalid file, and a subsequent review finding.
  All 102 tests passed with `.venv/bin/python -m pytest -q -p no:cacheprovider`.
  `git diff --check` passed. The folder assessor was pushed as `b4143c1`.
- Manual verification in Warp: the built-in folder command matched the
  shell-loop baseline with DKIM off. It assessed 12 emails, flagged two for
  review, and reported zero import failures.
- Follow-up from clean `main` at `b4143c1`: added `--review-only` for folder
  text reports. It keeps review findings and import errors visible and counts
  the whole batch. The extended regression failed before implementation, then
  all 102 tests passed with `.venv/bin/python -m pytest -q -p no:cacheprovider`.
  `git diff --check` passed. Importer, test, and docs are uncommitted.
- Manual verification in Warp: the review filter displayed only the two
  review reports and retained the full batch count of 12 assessed, two
  requiring review, and zero import failures. DKIM was off.
- The review-only filter was pushed as `3df21ef`. A DKIM-enabled Warp
  rerun also assessed 12 messages with two requiring review and no import
  failures. The MissionSquare domain authenticated and its subdomain mismatch
  remained visible. TreasuryDirect had no valid matching DKIM signature.
- Follow-up from clean `main` at `3df21ef`: label destination subdomains
  in the text report. The regression failed before the change and covers
  a genuine subdomain and a similarly spelled unrelated domain. All 102
  tests passed with `.venv/bin/python -m pytest -q -p no:cacheprovider`,
  and `git diff --check` passed. Formatter, test, and docs are uncommitted.
- Manual Warp verification: the DKIM-enabled report labeled the
  MissionSquare destination as a subdomain and kept both messages in review.
  The batch showed 12 assessed, two requiring review, and zero import failures.
- The subdomain label was pushed as `906f5fe`.
- Follow-up from clean `main` at `906f5fe`: track individual findings in
  SQLite, with mark and reopen commands and a pending-only review queue.
  The saved-email regression failed before review IDs existed and now
  verifies retention across imports, isolation between messages, and reopening.
  All 103 tests passed with `.venv/bin/python -m pytest -q -p no:cacheprovider`.
  `git diff --check` passed. Store, importer, formatter, tests, and docs
  are uncommitted.
- Manual verification in Warp: marking one TreasuryDirect finding hid
  only that finding across batch runs. After reopening the other finding,
  it appeared as pending while the first stayed hidden. MissionSquare
  remained pending and the original verdict totals stayed at 12 assessed,
  two requiring review, and zero import failures.
- Finding review tracking was pushed as `24bc2be`.
- Follow-up from clean `main` at `24bc2be`: save the latest assessment for
  each distinct email and expose pending findings via `--review-queue`.
  The new regression failed before implementation and now verifies the
  queue after removing the original, deduplication, marking, and reopening.
  All 104 tests passed with `.venv/bin/python -m pytest -q -p no:cacheprovider`.
  `git diff --check` passed. Store, importer, tests, and docs are uncommitted.
- Manual verification in Warp: after assessing the 12-email folder, the
  saved queue opened with only its database path and showed the MissionSquare
  and TreasuryDirect reports, two messages with pending findings.
- The saved queue was pushed as `8769ebb`.
- Follow-up from clean `main` at `8769ebb`: the saved queue shows message IDs
  and `--mark-message-reviewed` marks pending findings for one current
  snapshot. The new regression failed before implementation and now covers
  marking two findings, repeating the command, and preserving another
  message's findings. All 105 tests passed with
  `.venv/bin/python -m pytest -q -p no:cacheprovider`. Whitespace check passed.
- Manual verification in Warp: marking TreasuryDirect's message ID reviewed
  cleared both of its pending findings in one command. MissionSquare
  remained in the saved queue after its earlier finding was reopened.
- Message-level review was pushed as `7d1a3ea`.
- Follow-up from clean `main` at `7d1a3ea`: the saved reviewed view shows
  reviewed findings, IDs, and timestamps. The extended regression failed
  before the option existed and now verifies that reopening moves only the
  selected finding back to pending. The full suite passed all 105 tests with
  `.venv/bin/python -m pytest -q -p no:cacheprovider`. Whitespace check passed.
- Manual verification in Warp: the reviewed view showed both TreasuryDirect
  findings with their UTC review timestamps. MissionSquare was absent because
  its finding was still pending.
- The saved reviewed view was pushed as `9176cef`.
- Follow-up from clean `main` at `9176cef`: add optional local review notes
  to finding and message review, display them in text and JSON, and
  migrate older review tables. The extended regression failed before the
  option existed. All 105 tests passed afterward with
  `.venv/bin/python -m pytest -q -p no:cacheprovider`. Whitespace check passed.
- Manual verification in Warp: the existing SQLite database retained the
  earlier TreasuryDirect review timestamps. Marking MissionSquare with
  a note displayed that note only on its reviewed finding.
- Review notes were pushed as `0a9d6d8`.
- Follow-up from clean `main` at `0a9d6d8`: persist review and reopen
  events and expose them by finding ID. Existing reviewed states are
  backfilled with available timestamps and notes. The new regression
  failed before implementation and covers review, repeat, reopen, and
  whole-message review. All 106 tests passed with
  `.venv/bin/python -m pytest -q -p no:cacheprovider`. Whitespace check passed.
- Manual verification in Warp: reopening the MissionSquare finding on
  the existing test database preserved its original review event and
  note, followed by a new UTC reopen event.
- Finding review history was pushed as `89fadc3`.
- Follow-up from clean `main` at `89fadc3`: add message-level history
  grouped by finding. The extended regression failed before the option
  existed. All 106 tests passed afterward with
  `.venv/bin/python -m pytest -q -p no:cacheprovider`. Whitespace check passed.
- Manual verification in Warp: message history returned both TreasuryDirect
  link findings with their own evidence and review timestamps.
- Message history was pushed as `1919016`.
- Follow-up from clean `main` at `1919016`: add `--compact` to the saved
  review queue. The extended regression failed before implementation and
  passed afterward. All 106 tests passed with
  `.venv/bin/python -m pytest -q -p no:cacheprovider`. Whitespace check passed.
- Manual verification in Warp: the compact saved queue displayed the
  MissionSquare message ID, filename, and one pending finding on one line,
  followed by the one-message queue total.
- The compact queue was pushed as `97f375e`.
- Follow-up from clean `main` at `97f375e`: open a saved assessment by
  Message ID with current review state. The extended regression failed
  before the option was added and passed afterward. All 106 tests passed
  with `.venv/bin/python -m pytest -q -p no:cacheprovider`. Whitespace check passed.
- Manual verification in Warp: saved assessment lookup by Message ID
  displayed both reviewed TreasuryDirect findings, their UTC review
  timestamps, and their domain evidence.
- Saved assessment lookup was pushed as `bd45c6c`.
- Follow-up from clean `main` at `bd45c6c`: add an interactive review session
  that keeps one database selected and uses the existing queue, lookup,
  review, and history commands. The regression failed before the module
  existed, then all 107 tests passed with
  `.venv/bin/python -m pytest -q -p no:cacheprovider`. Whitespace checks passed.
- Manual verification in Warp: the interactive session displayed help, the
  pending MissionSquare message, and the reviewed TreasuryDirect findings
  from the same selected database. A second session opened the MissionSquare
  assessment and showed its review note and reopen event. Both exited with
  `quit`. Marking reviewed is covered by the automated session test.
- Interactive session verification was recorded in `9b6cb80`.

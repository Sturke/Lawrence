# Gatekeeper Email Assessment 1.0

Run `python3 -m tools.gatekeeper_import saved.eml --assess --database /path/to/gatekeeper.sqlite3`
to import one local message and emit a JSON review record to stdout. The existing
import rules apply. Assessment reads the decoded subject and plain-text body when available.
The `From` and `Date` headers are self-reported. Attachments are outside
assessment coverage. When an HTML alternative is available, Gatekeeper compares
domain names shown as link labels with their HTTP or HTTPS destination hostnames.

## 1.0 release notes

Gatekeeper 1.0 is the first release of the local saved-email workflow.
Import a saved `.eml` with a plain-text or HTML body and choose the default JSON
assessment or the readable terminal report. Gatekeeper recognizes supported
account sign-in, password reset, and password change notices, preserves
evidence for its findings, and reports which checks could run.

Save exact address approvals in SQLite. With optional DKIM verification,
the report can authenticate the claimed From domain for an individual message.
Address approval, domain authentication, and risk remain separate.
Domain authentication does not verify mailbox identity or the message's
claims. An inconclusive risk result means risk is unknown. The workflow
assesses saved files and takes no inbox actions.

Release validation covered the saved Apple notice with and without DKIM and
a synthetic credential request that required review. See
[project status](project_status.md) for the results.

## Manual test with saved emails

In Warp, run this setup command by itself and press Return. Run it once per test session.

```bash
cd ~/GitHub/Butler && demo_dir="$(mktemp -d)"
```
Paste the assessment command, add a space, and drag a saved `.eml` file from
Finder into Warp to insert its path. Then press Return. Repeat the assessment
command for the second file in the same Warp tab.

```bash
.venv/bin/python -m tools.gatekeeper_import --assess --database "$demo_dir/gatekeeper.sqlite3"
```

Both runs use the same temporary database. Compare `checks` to see what
Gatekeeper could evaluate for each email.

## Recognized message types

The `recognized` list labels the apparent purpose of an email.
`account_sign_in_notice` matches supported subject patterns such as
“Your Example Account was used to sign in to Example Cloud” and “New sign-in
to your account.” Each match quotes the subject as unverified local evidence.
Subjects that match no supported pattern produce an empty list. A recognized type can accompany any risk
disposition. Sender identity and the reported sign-in remain unverified.

Each recognized notice includes a `details` object. In the subject pattern
“Your … Account was used to sign in to …”, the text after “sign in to” supplies
`service`, and an optional “via …” supplies `sign_in_method`. Fields without
a value in the supported pattern are omitted. For example, “New sign-in to
your account” yields an empty `details` object. The quoted subject is the
unverified evidence for these extracted values.

`password_reset_notice` matches the complete subject “Password reset request”,
“Password reset requested”, “Reset your password”, or “Reset Password”, ignoring case and an
optional final period or exclamation mark. It quotes the subject as unverified
evidence and returns an empty `details` object.

`password_change_notice` matches “Password changed”, “Your password was
changed”, “Your password has been changed”, or “Your password has been
updated”, or “Your <service> password has been changed” as complete subjects, ignoring case and an optional final period
or exclamation mark. It quotes the subject
as unverified evidence and returns an empty `details` object.

A subject such as “New Device Logged In From macOS” is also recognized as an
account sign-in notice. The text after “From” is recorded as `platform` and
shown as the reported platform in the text report. The subject remains
unverified evidence.

## Phrase checks

| Category | v0.1 signal |
| --- | --- |
| `credential_request` | “verify your password” or “enter your password” |
| `payment_request` | “wire transfer” or “gift card” / “gift cards” |

Rules match whole phrases case-insensitively with flexible whitespace.
Each category appears at most once, with the first matching subject excerpt
or, failing that, the first matching body excerpt. Each finding gives its
category, confidence, reason, and separate evidence with field, exact excerpt,
source type `local_email`, and verification status `unverified`.

## Reply-To domain check

Gatekeeper compares the `From` and `Reply-To` domains without regard to
capitalization when each header provides one unambiguous address. If the
domains differ, the assessment returns `review_required` with a low-confidence
`reply_to_domain_mismatch` finding. The evidence includes `from_domain` and
`reply_to_domain`. Legitimate senders can use a different reply domain.

Matching domains produce no mismatch finding. If either domain is unavailable,
Gatekeeper skips this check.

For a local `.eml` with an HTML body or alternative,
Gatekeeper compares links whose entire label is a domain name with their
HTTP or HTTPS destination hostnames. The comparison ignores case. A mismatch
produces a low-confidence `link_domain_mismatch` finding with
`displayed_domain` and `destination_domain` as unverified evidence. The check
reads the HTML locally without rendering it or opening links.

The record includes `version`, the stored `message_id`, `disposition`,
`confidence`, `reason`, `findings`, `recognized`, `checks`, and `limitations`. The `version` field identifies the assessment rules used to produce the record. A match yields
`review_required` with `low` confidence. When no signal is found, the result is `inconclusive` with `low` confidence and an empty findings list. Confidence describes the
risk inference. A phrase alone supports only low confidence, including when
several phrases match. The record offers no clearance or sender authentication.

Review the quoted evidence in the original message and verify requests through
a trusted channel. JSON can be saved by the caller. SQLite stores the imported
message. By default, assessments run offline. Gatekeeper takes no inbox actions.


The `checks` object describes which domain comparisons ran for this message.

- `reply_to_domains` reports `compared` when both header domains were usable.
  Otherwise it reports `skipped` with reason `from_or_reply_to_domain_unavailable`.
- `html_link_domains` reports the number of eligible links in `links_compared`,
  including links whose domains match. A positive count has status `compared`.
  A zero count has status `skipped` with reason `html_body_unavailable` when
  there was no usable HTML body, or `no_eligible_links` when HTML was read
  but yielded no eligible links.

Use `findings` for signals that triggered review.


## Sender trust

Use the repeatable `--approved-sender ADDRESS` option with `--assess` to
supply exact approved addresses for the current run. The `sender_trust`
record reports the claimed mailbox from the `From` header and whether it
exactly matches an approved address. Gatekeeper requires one unambiguous
mailbox to report a claimed address.

An address match leaves mailbox identity `unverified`. Results written in the
exported message do not establish authentication. Sender trust is reported
separately from the existing risk disposition.


To persist an approval, use the sender management commands. They share the
importer's default SQLite database. For an isolated test, pass the same
`--database` path to both tools.

```bash
.venv/bin/python -m tools.gatekeeper_senders approve notices@example.com
.venv/bin/python -m tools.gatekeeper_senders list
.venv/bin/python -m tools.gatekeeper_senders remove notices@example.com
```

Approvals store the exact address and its UTC approval time. Assessments
consult saved approvals along with any addresses supplied for that command.


## Optional DKIM verification

Install the optional verifier with `python -m pip install -r requirements-dkim.txt`
in the environment you use to run Gatekeeper. Add `--verify-dkim` alongside
`--assess` to check the original message bytes against public DKIM keys via DNS.
The message stays local. DNS queries reveal the signing domain and key selector.

`sender_domain_authentication` reports `authenticated` only for a valid,
full-body RSA-SHA256 signature whose signing domain exactly matches the
single From mailbox's domain. It reports `unverified` with a reason if that
evidence is unavailable, and `not_checked` when the flag was omitted.
Address approval, mailbox identity, and risk disposition are reported separately.

## Readable terminal report

Add `--format text` with `--assess` to see the recognized message type,
address approval, sender domain authentication, and message risk on separate
lines. Risk findings appear under the verdict. For each link domain mismatch,
the report shows the displayed domain and the destination hostname. Add `--verify-dkim` when you
want the report to include a live DNS verification result. JSON remains the
default and includes the full evidence and assessment limitations.


For HTML-only mail, Gatekeeper checks the subject, eligible links, and
extracted HTML text. Text extraction skips head, script, style, and template
content and does not render the email or evaluate CSS visibility. Phrase
findings from that text use the evidence field `html_body_text`. JSON reports
plain-text and HTML phrase coverage separately. The stored plain-text body
is empty.

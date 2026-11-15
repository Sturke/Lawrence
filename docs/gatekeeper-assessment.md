# Gatekeeper Email Assessment v0.1

Run `python3 -m tools.gatekeeper_import saved.eml --assess --database /path/to/gatekeeper.sqlite3`
to import one local message and emit a JSON review record to stdout. The existing
import rules apply. Assessment reads the decoded subject and plain-text body.
Sender and Date are self-reported. Attachments and HTML are outside assessment coverage.

| Category | v0.1 signal |
| --- | --- |
| `credential_request` | “verify your password” or “enter your password” |
| `payment_request` | “wire transfer” or “gift card” / “gift cards” |

Rules match whole phrases case-insensitively with flexible whitespace.
Each category appears at most once, with the first matching subject excerpt
or, failing that, the first matching body excerpt. Each finding gives its
category, confidence, reason, and separate evidence with field, exact excerpt,
source type `local_email`, and verification status `unverified`.

The record includes `version`, the stored `message_id`, `disposition`,
`confidence`, `reason`, `findings`, and `limitations`. A match yields
`review_required` with `low` confidence. Zero matches yields `inconclusive`
with `low` confidence and an empty findings list. Confidence describes the
risk inference. A phrase alone supports only low confidence, including when
several phrases match. The record offers no clearance or sender authentication.

Review the quoted evidence in the original message and verify requests through
a trusted channel. JSON can be saved by the caller. SQLite stores the imported
message. The assessment makes no network requests and takes no inbox actions.

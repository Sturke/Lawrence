# Gatekeeper Email Assessment v0.3

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

## Reply-To domain check

Gatekeeper compares the `From` and `Reply-To` domains without regard to
capitalization when each header provides one unambiguous address. If the
domains differ, the assessment returns `review_required` with a low-confidence
`reply_to_domain_mismatch` finding. The evidence includes `from_domain` and
`reply_to_domain`. Legitimate senders can use a different reply domain.

Matching domains produce no mismatch finding. If either domain is unavailable,
Gatekeeper skips this check.

For a local `.eml` with both a plain-text body and an HTML alternative,
Gatekeeper compares links whose entire label is a domain name with their
HTTP or HTTPS destination hostnames. The comparison ignores case. A mismatch
produces a low-confidence `link_domain_mismatch` finding with
`displayed_domain` and `destination_domain` as unverified evidence. The check
reads the HTML locally without rendering it or opening links.

The record includes `version`, the stored `message_id`, `disposition`,
`confidence`, `reason`, `findings`, and `limitations`. The `version` field identifies the assessment rules used to produce the record. A match yields
`review_required` with `low` confidence. When no signal is found, the result is `inconclusive` with `low` confidence and an empty findings list. Confidence describes the
risk inference. A phrase alone supports only low confidence, including when
several phrases match. The record offers no clearance or sender authentication.

Review the quoted evidence in the original message and verify requests through
a trusted channel. JSON can be saved by the caller. SQLite stores the imported
message. The assessment makes no network requests and takes no inbox actions.

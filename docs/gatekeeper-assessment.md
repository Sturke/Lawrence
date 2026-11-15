# Gatekeeper Email Assessment v0.4

Run `python3 -m tools.gatekeeper_import saved.eml --assess --database /path/to/gatekeeper.sqlite3`
to import one local message and emit a JSON review record to stdout. The existing
import rules apply. Assessment reads the decoded subject and plain-text body.
The `From` and `Date` headers are self-reported. Attachments are outside
assessment coverage. When an HTML alternative is available, Gatekeeper compares
domain names shown as link labels with their HTTP or HTTPS destination hostnames.

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

For a local `.eml` with both a plain-text body and an HTML alternative,
Gatekeeper compares links whose entire label is a domain name with their
HTTP or HTTPS destination hostnames. The comparison ignores case. A mismatch
produces a low-confidence `link_domain_mismatch` finding with
`displayed_domain` and `destination_domain` as unverified evidence. The check
reads the HTML locally without rendering it or opening links.

The record includes `version`, the stored `message_id`, `disposition`,
`confidence`, `reason`, `findings`, `checks`, and `limitations`. The `version` field identifies the assessment rules used to produce the record. A match yields
`review_required` with `low` confidence. When no signal is found, the result is `inconclusive` with `low` confidence and an empty findings list. Confidence describes the
risk inference. A phrase alone supports only low confidence, including when
several phrases match. The record offers no clearance or sender authentication.

Review the quoted evidence in the original message and verify requests through
a trusted channel. JSON can be saved by the caller. SQLite stores the imported
message. The assessment makes no network requests and takes no inbox actions.


The `checks` object describes which domain comparisons ran for this message.

- `reply_to_domains` reports `compared` when both header domains were usable.
  Otherwise it reports `skipped` with reason `from_or_reply_to_domain_unavailable`.
- `html_link_domains` reports the number of eligible links in `links_compared`,
  including links whose domains match. A positive count has status `compared`.
  A zero count has status `skipped` with reason `html_body_unavailable` when
  there was no usable HTML body, or `no_eligible_links` when HTML was read
  but yielded no eligible links.

Use `findings` for signals that triggered review.

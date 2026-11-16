"""Import one saved email without connecting to an inbox."""

import argparse
import json
import sqlite3
from collections import Counter
from hashlib import sha256
from email import policy
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
from pathlib import Path

from memory.gatekeeper import DEFAULT_DATABASE, MessageStore
from verification.dkim_authentication import authenticate_from_domain
from verification.email_assessment import assess_email
from verification.email_report import format_email_report


def single_mailbox(message, header_name):
    """Return the address when the header has one unambiguous mailbox."""
    headers = message.get_all(header_name, [])
    if len(headers) != 1:
        return None

    header = headers[0]
    if header.defects or len(header.addresses) != 1:
        return None

    address = header.addresses[0]
    if not address.username or not address.domain:
        return None

    return address


def read_email(path, *, domains=None, verify_dkim=False):
    """Extract a saved email with a plain-text or HTML body.

    The Date header is the sender's date, not a verified delivery timestamp.
    Attachments are not imported. HTML is never rendered or fetched.
    """
    raw = Path(path).read_bytes()
    message = BytesParser(policy=policy.default).parsebytes(raw)
    sender = str(message.get("From", "")).strip()
    html_part = message.get_body(preferencelist=("html",))
    if domains is not None:
        domains["message_digest"] = sha256(raw).hexdigest()
        from_address = single_mailbox(message, "From")
        reply_to_address = single_mailbox(message, "Reply-To")
        if from_address is not None:
            domains["claimed_address"] = from_address.addr_spec
            domains["from_domain"] = from_address.domain.casefold()
        if reply_to_address is not None:
            domains["reply_to_domain"] = reply_to_address.domain.casefold()
        if html_part is not None:
            try:
                domains["html_body"] = html_part.get_content()
            except (LookupError, UnicodeError):
                domains["html_body"] = None
    if not sender:
        raise ValueError("Email must have a From header")
    try:
        date = parsedate_to_datetime(str(message.get("Date", "")))
    except (ValueError, TypeError, OverflowError) as error:
        raise ValueError("Email must have a valid Date header with timezone") from error
    if date.tzinfo is None:
        raise ValueError("Email Date header must include a known timezone")
    part = message.get_body(preferencelist=("plain",))
    if part is None:
        if html_part is None:
            raise ValueError("Email must contain a plain-text or HTML body")
        body = ""
        if domains is not None:
            domains["plain_text_available"] = False
    else:
        try:
            body = part.get_content()
        except (LookupError, UnicodeError) as error:
            raise ValueError("Email body could not be decoded") from error
    if verify_dkim and domains is not None:
        domains["sender_domain_authentication"] = authenticate_from_domain(
            raw, message, domains.get("from_domain")
        )
    return {
        "sender": sender,
        "subject": str(message.get("Subject", "")),
        "body": body,
        "received_at": date.isoformat(),
    }


def import_email(path, store):
    """Save one email and return its local ID; repeated imports create rows."""
    return store.save_message(**read_email(path))


def add_finding_review_states(record, message_digest, store):
    occurrences = Counter()
    review_ids = []
    for finding in record["findings"]:
        evidence = json.dumps(
            [finding["category"], finding["evidence"]], sort_keys=True
        )
        occurrences[evidence] += 1
        key = json.dumps([message_digest, evidence, occurrences[evidence]])
        review_ids.append(sha256(key.encode("utf-8")).hexdigest())
    if review_ids:
        states = store.finding_review_states(review_ids)
        for finding, review_id in zip(record["findings"], review_ids, strict=True):
            finding.update(review_id=review_id, reviewed_at=states[review_id])


def import_one(path, args):
    domains = {} if args.assess else None
    message = read_email(path, domains=domains, verify_dkim=args.verify_dkim)
    database = args.database.expanduser()
    database.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    store = MessageStore(database)
    if args.assess:
        approved_senders = set(args.approved_sender)
        approved_senders.update(row["address"] for row in store.list_approved_senders())
    message_id = store.save_message(**message)
    record = None
    if args.assess:
        message_digest = domains.pop("message_digest")
        record = assess_email(
            message_id, message, approved_senders=approved_senders, **domains
        )
        add_finding_review_states(record, message_digest, store)
        store.save_review_snapshot(message_digest, path.name, record)
    return message_id, record


def assess_folder(args):
    folder = args.folder.expanduser()
    paths = sorted(
        path for path in folder.iterdir()
        if path.suffix.lower() == ".eml" and not path.is_symlink() and path.is_file()
    )
    results = []
    summary = {"assessed": 0, "review_required": 0, "import_failures": 0}
    for path in paths:
        result = {"file": path.name}
        try:
            _, record = import_one(path, args)
        except (OSError, ValueError, sqlite3.Error) as error:
            result["error"] = str(error)
            summary["import_failures"] += 1
        else:
            result["assessment"] = record
            summary["assessed"] += 1
            if record["disposition"] == "review_required":
                summary["review_required"] += 1
        results.append(result)

    if args.format != "text":
        print(json.dumps({"results": results, "summary": summary}))
        return
    pending_messages = 0
    for result in results:
        record = result.get("assessment")
        if args.review_only and record is not None:
            pending = [finding for finding in record["findings"] if not finding["reviewed_at"]]
            if not pending:
                continue
            pending_messages += 1
            record = dict(record, findings=pending)
        print(f'=== {json.dumps(result["file"])} ===')
        if "error" in result:
            print(f'Import failed: {json.dumps(result["error"])}')
        else:
            print(format_email_report(record))
        print()
    print(
        f'Batch summary: {summary["assessed"]} assessed · '
        f'{summary["review_required"]} require review · '
        f'{summary["import_failures"]} import failures'
    )

    if args.review_only:
        print(f"Review queue: {pending_messages} messages with pending findings.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("email", nargs="?", type=Path, help="Path to a saved .eml file")
    inputs.add_argument("--folder", type=Path, help="Assess .eml files in this folder")
    inputs.add_argument("--reviewed", action="store_true", help="Show saved reviewed findings")
    inputs.add_argument("--review-queue", action="store_true", help="Show saved pending findings")
    inputs.add_argument(
        "--mark-message-reviewed", type=int, metavar="MESSAGE_ID",
        help="Mark all pending findings on one saved message reviewed",
    )
    inputs.add_argument("--mark-reviewed", metavar="ID", help="Mark one known finding reviewed")
    inputs.add_argument("--reopen-review", metavar="ID", help="Reopen one known finding")
    parser.add_argument(
        "--database", type=Path,
        default=DEFAULT_DATABASE,
        help="SQLite file (default: ~/Library/Application Support/Butler/gatekeeper.sqlite3)",
    )
    parser.add_argument("--assess", action="store_true", help="Emit a JSON review record")
    parser.add_argument(
        "--approved-sender", action="append", default=[], metavar="ADDRESS",
        help="Exact approved address for this assessment (repeatable)",
    )
    parser.add_argument("--verify-dkim", action="store_true", help="Verify DKIM using DNS")
    parser.add_argument(
        "--format", choices=("json", "text"), help="Assessment output format (default: json)",
    )
    parser.add_argument(
        "--review-only", action="store_true",
        help="Show only review findings and import errors in folder text reports",
    )
    args = parser.parse_args(argv)
    if args.review_only and (args.folder is None or args.format != "text"):
        parser.error("--review-only requires --folder and --format text")
    if args.format is not None and not (args.assess or args.review_queue or args.reviewed):
        parser.error("--format requires --assess, --review-queue, or --reviewed")
    if args.verify_dkim and not args.assess:
        parser.error("--verify-dkim requires --assess")
    if args.approved_sender and not args.assess:
        parser.error("--approved-sender requires --assess")
    if args.review_queue or args.reviewed:
        if args.assess:
            parser.error("Saved review views cannot be combined with --assess")
        database = args.database.expanduser()
        try:
            results = (
                MessageStore(database).review_snapshots(show_reviewed=args.reviewed)
                if database.exists() else []
            )
        except (OSError, ValueError, sqlite3.Error) as error:
            parser.exit(1, f"Review queue failed: {error}\n")
        if args.format == "text":
            for result in results:
                print(f'=== {json.dumps(result["file"])} ===')
                print(f'Message ID: {result["assessment"]["message_id"]}')
                print(format_email_report(result["assessment"]))
                print()
            noun = "message" if len(results) == 1 else "messages"
            if args.reviewed:
                print(f"Reviewed view: {len(results)} {noun} with reviewed findings.")
            else:
                print(f"Review queue: {len(results)} {noun} with pending findings.")
        else:
            count_key = "reviewed_messages" if args.reviewed else "pending_messages"
            print(json.dumps({"results": results, count_key: len(results)}))
        return
    if args.mark_message_reviewed is not None:
        if args.assess:
            parser.error("--mark-message-reviewed cannot be combined with --assess")
        database = args.database.expanduser()
        try:
            count = (
                MessageStore(database).mark_message_reviewed(args.mark_message_reviewed)
                if database.is_file() else None
            )
        except (OSError, ValueError, OverflowError, sqlite3.Error) as error:
            parser.exit(1, f"Review update failed: {error}\n")
        if count is None:
            parser.exit(1, "Message ID not found among current saved assessments. Open the queue for current IDs.\n")
        noun = "finding" if count == 1 else "findings"
        print(f"{count} {noun} marked reviewed.")
        return
    if args.mark_reviewed is not None or args.reopen_review is not None:
        if args.assess:
            parser.error("Review actions cannot be combined with --assess")
        review_id = args.mark_reviewed if args.mark_reviewed is not None else args.reopen_review
        database = args.database.expanduser()
        try:
            found = database.is_file() and MessageStore(database).set_finding_reviewed(
                review_id, args.mark_reviewed is not None
            )
        except (OSError, ValueError, sqlite3.Error) as error:
            parser.exit(1, f"Review update failed: {error}\n")
        if not found:
            parser.exit(1, "Finding ID not found in this database.\n")
        print("Finding marked reviewed." if args.mark_reviewed is not None else "Finding reopened.")
        return
    if args.folder is not None:
        if not args.assess:
            parser.error("--folder requires --assess")
        try:
            assess_folder(args)
        except OSError as error:
            parser.exit(1, f"Folder assessment failed: {error}\n")
        return

    try:
        message_id, record = import_one(args.email.expanduser(), args)
    except (OSError, ValueError, sqlite3.Error) as error:
        parser.exit(1, f"Import failed: {error}\n")
    if record is not None:
        print(format_email_report(record) if args.format == "text" else json.dumps(record))
    else:
        print(f"Stored message {message_id} in {args.database.expanduser()}")

if __name__ == "__main__":
    main()

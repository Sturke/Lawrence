"""Import one saved email without connecting to an inbox."""

import argparse
import json
import sqlite3
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
    """Extract a plain-text email; reject missing sender/date or HTML-only mail.

    The Date header is the sender's date, not a verified delivery timestamp.
    Attachments are not imported. HTML is never rendered or fetched.
    """
    raw = Path(path).read_bytes()
    message = BytesParser(policy=policy.default).parsebytes(raw)
    sender = str(message.get("From", "")).strip()
    if domains is not None:
        from_address = single_mailbox(message, "From")
        reply_to_address = single_mailbox(message, "Reply-To")
        if from_address is not None:
            domains["claimed_address"] = from_address.addr_spec
            domains["from_domain"] = from_address.domain.casefold()
        if reply_to_address is not None:
            domains["reply_to_domain"] = reply_to_address.domain.casefold()
        html_part = message.get_body(preferencelist=("html",))
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
        raise ValueError("Email must contain a plain-text body; HTML-only mail is unsupported")
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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("email", type=Path, help="Path to a saved .eml file")
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
    args = parser.parse_args(argv)
    if args.format is not None and not args.assess:
        parser.error("--format requires --assess")
    if args.verify_dkim and not args.assess:
        parser.error("--verify-dkim requires --assess")
    if args.approved_sender and not args.assess:
        parser.error("--approved-sender requires --assess")
    try:
        # Validate the input before creating any persistent storage.
        domains = {} if args.assess else None
        message = read_email(
            args.email.expanduser(), domains=domains, verify_dkim=args.verify_dkim
        )
        database = args.database.expanduser()
        database.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        store = MessageStore(database)
        if args.assess:
            approved_senders = set(args.approved_sender)
            approved_senders.update(row["address"] for row in store.list_approved_senders())
        message_id = store.save_message(**message)
    except (OSError, ValueError, sqlite3.Error) as error:
        parser.exit(1, f"Import failed: {error}\n")
    if args.assess:
        record = assess_email(
            message_id, message, approved_senders=approved_senders, **domains
        )
        print(format_email_report(record) if args.format == "text" else json.dumps(record))
    else:
        print(f"Stored message {message_id} in {database}")


if __name__ == "__main__":
    main()

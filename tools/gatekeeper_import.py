"""Import one saved email without connecting to an inbox."""

import argparse
import sqlite3
from email import policy
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
from pathlib import Path

from memory.gatekeeper import MessageStore


def read_email(path):
    """Extract a plain-text email; reject missing sender/date or HTML-only mail.

    The Date header is the sender's date, not a verified delivery timestamp.
    Attachments are not imported. HTML is never rendered or fetched.
    """
    with Path(path).open("rb") as source:
        message = BytesParser(policy=policy.default).parse(source)
    sender = str(message.get("From", "")).strip()
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
        default=Path("~/Library/Application Support/Butler/gatekeeper.sqlite3"),
        help="SQLite file (default: ~/Library/Application Support/Butler/gatekeeper.sqlite3)",
    )
    args = parser.parse_args(argv)
    try:
        # Validate the input before creating any persistent storage.
        message = read_email(args.email.expanduser())
        database = args.database.expanduser()
        database.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        message_id = MessageStore(database).save_message(**message)
    except (OSError, ValueError, sqlite3.Error) as error:
        parser.exit(1, f"Import failed: {error}\n")
    print(f"Stored message {message_id} in {database}")


if __name__ == "__main__":
    main()

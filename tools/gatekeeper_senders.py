"""Manage local sender address approvals for Gatekeeper."""

import argparse
import json
import sqlite3
from email.errors import HeaderParseError
from email.headerregistry import Address
from pathlib import Path

from memory.gatekeeper import DEFAULT_DATABASE, MessageStore


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("approve").add_argument("address")
    commands.add_parser("list")
    commands.add_parser("remove").add_argument("address")
    args = parser.parse_args(argv)

    if args.command != "list":
        try:
            mailbox = Address(addr_spec=args.address)
            if not mailbox.username or not mailbox.domain or mailbox.addr_spec != args.address:
                raise ValueError("expected one exact mailbox address")
        except (ValueError, HeaderParseError, IndexError):
            parser.error("provide a single mailbox address such as notices@example.com")

    try:
        database = args.database.expanduser()
        database.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        store = MessageStore(database)
        if args.command == "approve":
            store.approve_sender(args.address)
            print(f"Approved address: {args.address}")
        elif args.command == "remove":
            removed = store.remove_sender_approval(args.address)
            print("Approval removed." if removed else "No matching approval.")
        else:
            print(json.dumps(store.list_approved_senders()))
    except (OSError, ValueError, sqlite3.Error) as error:
        parser.exit(1, f"Sender approval command failed: {error}\n")


if __name__ == "__main__":
    main()

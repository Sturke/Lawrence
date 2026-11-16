"""Review saved Gatekeeper assessments in an interactive terminal session."""

import argparse
import re
import shlex
import sys
from pathlib import Path

from memory.gatekeeper import DEFAULT_DATABASE
from tools.gatekeeper_import import main as run_gatekeeper


HELP = """queue                   List messages with pending findings
show MESSAGE_ID         Open a saved assessment
done MESSAGE_ID [NOTE]  Mark pending findings reviewed; quote a note with spaces
history MESSAGE_ID      Show review history for a message
reviewed                List reviewed findings
help                    Show these commands
quit                    End the session"""


def review_arguments(words):
    command, *values = words
    if command == "queue" and not values:
        return ["--review-queue", "--compact"]
    if command == "reviewed" and not values:
        return ["--reviewed", "--format", "text"]
    if command not in {"show", "done", "history"}:
        raise ValueError("Unknown command or unexpected arguments. Enter help.")
    if not values or not re.fullmatch(r"[0-9]+", values[0]):
        raise ValueError("Enter the numeric Message ID shown in the queue.")
    message_id, *note = values
    if note and (command != "done" or len(note) != 1):
        raise ValueError('Use done MESSAGE_ID "optional note", or enter help.')
    if command == "show":
        return ["--show-message", message_id, "--format", "text"]
    if command == "history":
        return ["--message-history", message_id]
    args = ["--mark-message-reviewed", message_id]
    if note:
        args.append(f"--review-note={note[0]}")
    return args


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    database = str(parser.parse_args(argv).database.expanduser().resolve())
    print("Gatekeeper review session. Enter help for commands, or quit to exit.")
    while True:
        try:
            words = shlex.split(input("gatekeeper> "))
        except (EOFError, KeyboardInterrupt):
            print()
            return
        except ValueError as error:
            print(f"Invalid command: {error}", file=sys.stderr)
            continue
        if not words:
            continue
        if words == ["quit"]:
            return
        if words == ["help"]:
            print(HELP)
            continue
        try:
            args = review_arguments(words)
        except ValueError as error:
            print(error, file=sys.stderr)
            continue
        try:
            run_gatekeeper([*args, "--database", database])
        except SystemExit:
            # An invalid command or missing assessment should leave the prompt open.
            continue


if __name__ == "__main__":
    main()

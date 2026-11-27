"""Move selected saved emails into and out of a local quarantine folder."""

import argparse
import errno
import json
import os
import stat
from pathlib import Path

from memory.gatekeeper import DEFAULT_DATABASE


DEFAULT_QUARANTINE = DEFAULT_DATABASE.parent / "quarantine"


def move_saved_email(source, target):
    if source.suffix.lower() != ".eml" or not stat.S_ISREG(source.lstat().st_mode):
        raise ValueError("select a regular .eml file")

    # Creating the destination link is exclusive. The source remains in place
    # if the destination exists or the filesystem cannot create the link.
    try:
        os.link(source, target, follow_symlinks=False)
    except FileExistsError as error:
        raise ValueError(f"destination already exists: {target}") from error
    except OSError as error:
        if error.errno == errno.EXDEV:
            raise ValueError("source and destination must be on the same filesystem") from error
        raise

    try:
        source.unlink()
    except OSError as error:
        raise ValueError(
            f"destination was created at {target}, but removing the source failed: {error}"
        ) from error


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=DEFAULT_QUARANTINE)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("move", help="Quarantine one saved email").add_argument("email", type=Path)
    commands.add_parser("list", help="List quarantined email filenames")
    restore = commands.add_parser("restore", help="Restore one quarantined email")
    restore.add_argument("filename")
    restore.add_argument("destination", type=Path, help="Existing folder to restore into")
    args = parser.parse_args(argv)

    try:
        directory = args.directory.expanduser().resolve()
        if directory.exists() and not directory.is_dir():
            raise ValueError("quarantine path must be a directory")
        if args.command == "list":
            filenames = sorted(
                entry.name for entry in directory.iterdir()
                if entry.suffix.lower() == ".eml" and stat.S_ISREG(entry.lstat().st_mode)
            ) if directory.exists() else []
            print(json.dumps(filenames))
            return

        if args.command == "move":
            source = args.email.expanduser()
            if source.parent.resolve().is_relative_to(directory):
                raise ValueError("the source is already inside the quarantine folder")
            directory.mkdir(mode=0o700, parents=True, exist_ok=True)
            target = directory / source.name
        else:
            if Path(args.filename).name != args.filename or Path(args.filename).suffix.lower() != ".eml":
                raise ValueError("use a quarantined .eml filename from the list command")
            destination = args.destination.expanduser().resolve(strict=True)
            if not destination.is_dir() or destination.is_relative_to(directory):
                raise ValueError("restore into an existing folder outside quarantine")
            source = directory / args.filename
            target = destination / args.filename

        move_saved_email(source, target)
        print(json.dumps({"action": args.command, "path": str(target)}))
    except (OSError, ValueError) as error:
        parser.exit(1, f"Quarantine command failed: {error}\n")


if __name__ == "__main__":
    main()

"""Local persistence for Gatekeeper's email messages."""

import json
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path


DEFAULT_DATABASE = Path("~/Library/Application Support/Butler/gatekeeper.sqlite3")


class MessageStore:
    """Store messages in a SQLite file at a caller-selected path.

    The parent directory must exist. Each operation closes its connection;
    use a file path, not SQLite's connection-local ``:memory:`` database.
    """

    def __init__(self, database_path):
        self.database_path = str(database_path)
        if self.database_path in {"", ":memory:"}:
            raise ValueError("MessageStore requires a persistent database file path")
        with closing(sqlite3.connect(self.database_path)) as connection:
            with connection:
                connection.execute("""
                    CREATE TABLE IF NOT EXISTS gatekeeper_messages (
                        id INTEGER PRIMARY KEY,
                        sender TEXT NOT NULL,
                        subject TEXT NOT NULL,
                        body TEXT NOT NULL,
                        received_at TEXT NOT NULL
                    )
                """)

                connection.execute("""
                    CREATE TABLE IF NOT EXISTS gatekeeper_sender_approvals (
                        address TEXT NOT NULL PRIMARY KEY,
                        approved_at TEXT NOT NULL
                    )
                """)

                connection.execute("""
                    CREATE TABLE IF NOT EXISTS gatekeeper_finding_reviews (
                        review_id TEXT NOT NULL PRIMARY KEY,
                        reviewed_at TEXT
                    )
                """)

                connection.execute("""
                    CREATE TABLE IF NOT EXISTS gatekeeper_review_snapshots (
                        message_digest TEXT NOT NULL PRIMARY KEY,
                        message_id INTEGER NOT NULL,
                        filename TEXT NOT NULL,
                        assessment TEXT NOT NULL
                    )
                """)

    def save_review_snapshot(self, message_digest, filename, record):
        with closing(sqlite3.connect(self.database_path)) as connection, connection:
            connection.execute(
                """INSERT INTO gatekeeper_review_snapshots
                   (message_digest, message_id, filename, assessment) VALUES (?, ?, ?, ?)
                   ON CONFLICT(message_digest) DO UPDATE SET
                       message_id = excluded.message_id,
                       filename = excluded.filename,
                       assessment = excluded.assessment
                   WHERE excluded.message_id > gatekeeper_review_snapshots.message_id""",
                (message_digest, record["message_id"], filename, json.dumps(record)),
            )

    def review_snapshots(self, *, show_reviewed=False):
        with closing(sqlite3.connect(self.database_path)) as connection:
            connection.execute("BEGIN")
            reviewed = dict(connection.execute(
                "SELECT review_id, reviewed_at FROM gatekeeper_finding_reviews WHERE reviewed_at IS NOT NULL"
            ))
            results = []
            for filename, assessment in connection.execute(
                "SELECT filename, assessment FROM gatekeeper_review_snapshots ORDER BY message_id"
            ):
                record = json.loads(assessment)
                findings = [
                    dict(finding, reviewed_at=reviewed.get(finding["review_id"]))
                    for finding in record["findings"]
                    if (finding["review_id"] in reviewed) == show_reviewed
                ]
                if findings:
                    results.append({"file": filename, "assessment": dict(record, findings=findings)})
            return results

    def mark_message_reviewed(self, message_id):
        """Mark pending findings on the selected current snapshot."""
        with closing(sqlite3.connect(self.database_path)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT assessment FROM gatekeeper_review_snapshots WHERE message_id = ?",
                (message_id,),
            ).fetchone()
            if row is None:
                return None
            timestamp = datetime.now(UTC).isoformat()
            cursor = connection.executemany(
                """UPDATE gatekeeper_finding_reviews SET reviewed_at = ?
                   WHERE review_id = ? AND reviewed_at IS NULL""",
                ((timestamp, item["review_id"]) for item in json.loads(row[0])["findings"]),
            )
            return cursor.rowcount

    def finding_review_states(self, review_ids):
        with closing(sqlite3.connect(self.database_path)) as connection, connection:
            connection.executemany(
                "INSERT OR IGNORE INTO gatekeeper_finding_reviews (review_id) VALUES (?)",
                ((review_id,) for review_id in review_ids),
            )
            return {
                review_id: connection.execute(
                    "SELECT reviewed_at FROM gatekeeper_finding_reviews WHERE review_id = ?",
                    (review_id,),
                ).fetchone()[0]
                for review_id in review_ids
            }

    def set_finding_reviewed(self, review_id, reviewed):
        timestamp = datetime.now(UTC).isoformat() if reviewed else None
        with closing(sqlite3.connect(self.database_path)) as connection, connection:
            cursor = connection.execute(
                """UPDATE gatekeeper_finding_reviews SET reviewed_at =
                   CASE WHEN ? IS NULL THEN NULL ELSE COALESCE(reviewed_at, ?) END
                   WHERE review_id = ?""",
                (timestamp, timestamp, review_id),
            )
            return cursor.rowcount > 0

    def approve_sender(self, address):
        with closing(sqlite3.connect(self.database_path)) as connection, connection:
            connection.execute(
                """INSERT INTO gatekeeper_sender_approvals (address, approved_at)
                   VALUES (?, ?) ON CONFLICT(address) DO NOTHING""",
                (address, datetime.now(UTC).isoformat()),
            )

    def list_approved_senders(self):
        with closing(sqlite3.connect(self.database_path)) as connection:
            connection.row_factory = sqlite3.Row
            return [dict(row) for row in connection.execute(
                "SELECT address, approved_at FROM gatekeeper_sender_approvals ORDER BY address"
            )]

    def remove_sender_approval(self, address):
        with closing(sqlite3.connect(self.database_path)) as connection, connection:
            cursor = connection.execute(
                "DELETE FROM gatekeeper_sender_approvals WHERE address = ?", (address,)
            )
            return cursor.rowcount > 0

    def save_message(self, *, sender, subject, body, received_at):
        """Save an email and return its local ID.

        received_at is a caller-supplied ISO 8601 timestamp with timezone.
        Empty subjects/bodies are allowed. Repeated saves create new rows.
        """
        with closing(sqlite3.connect(self.database_path)) as connection:
            with connection:
                cursor = connection.execute(
                    """INSERT INTO gatekeeper_messages
                       (sender, subject, body, received_at) VALUES (?, ?, ?, ?)""",
                    (sender, subject, body, received_at),
                )
                return cursor.lastrowid

    def get_message(self, message_id):
        """Return a message dictionary, or None when its ID is unknown."""
        with closing(sqlite3.connect(self.database_path)) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                "SELECT id, sender, subject, body, received_at "
                "FROM gatekeeper_messages WHERE id = ?",
                (message_id,),
            ).fetchone()
            return dict(row) if row is not None else None

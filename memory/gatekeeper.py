"""Local persistence for Gatekeeper's email messages."""

import sqlite3
from contextlib import closing


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

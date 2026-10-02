"""Local persistence for Burke-approved personal memories."""

import sqlite3
from contextlib import closing
from datetime import datetime, timezone

class PersonalMemoryStore:
    """Store explicitly approved personal memories in a SQLite file."""

    def __init__(self, database_path):
        self.database_path = str(database_path)

        if self.database_path in {"", ":memory:"}:
            raise ValueError(
                "PersonalMemoryStore requires a persistent database file path"
            )

        with closing(sqlite3.connect(self.database_path)) as connection:
            with connection:
                connection.execute("""
                    CREATE TABLE IF NOT EXISTS personal_memories (
                        id INTEGER PRIMARY KEY,
                        content TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                """)

    def save_memory(self, *, content):
        """Save an explicitly approved personal memory and return its local ID."""
        

        created_at = datetime.now(timezone.utc).isoformat()

        with closing(sqlite3.connect(self.database_path)) as connection:
            with connection:
                cursor = connection.execute(
                    """INSERT INTO personal_memories
                       (content, created_at) VALUES (?, ?)""",
                    (content, created_at),
                )
                return cursor.lastrowid
            
    def get_memories(self):
        """Return all personal memories in the order they were stored."""
        with closing(sqlite3.connect(self.database_path)) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """SELECT id, content, created_at
                   FROM personal_memories
                   ORDER BY id"""
            ).fetchall()

            return [dict(row) for row in rows]
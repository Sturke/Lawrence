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

                existing_columns = {
                    row[1]
                    for row in connection.execute(
                        "PRAGMA table_info(personal_memories)"
                    )
                }

                structured_columns = {
                    "category": "TEXT",
                    "subject": "TEXT",
                    "value": "TEXT",
                    "updated_at": "TEXT",
                }

                for column, column_type in structured_columns.items():
                    if column not in existing_columns:
                        connection.execute(
                            f"ALTER TABLE personal_memories "
                            f"ADD COLUMN {column} {column_type}"
                        )

    def save_memory(
        self,
        *,
        content,
        category=None,
        subject=None,
        value=None,
    ):
        """Save an explicitly approved personal memory and return its local ID."""

        created_at = datetime.now(timezone.utc).isoformat()

        with closing(sqlite3.connect(self.database_path)) as connection:
            with connection:
                cursor = connection.execute(
                    """INSERT INTO personal_memories
                    (
                        content,
                        category,
                        subject,
                        value,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        content,
                        category,
                        subject,
                        value,
                        created_at,
                        created_at,
                    ),
                )
                return cursor.lastrowid
            
    def get_memories(self):
        """Return all personal memories in the order they were stored."""
        with closing(sqlite3.connect(self.database_path)) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """SELECT id, content, category, subject, value,
                    created_at, updated_at
                    FROM personal_memories
                    ORDER BY id"""
            ).fetchall()

            return [dict(row) for row in rows]

    def search_memories(self, *, query):
        """Return personal memories containing the query text."""
        query = query.lower()

        return [
            memory
            for memory in self.get_memories()
            if query in memory["content"].lower()
        ]

    def find_relevant_memories(self, *, query):
        """Return memories ranked by the number of words shared with the query."""
        query_words = {
            word.strip(".,?!").lower()
            for word in query.split()
            if len(word.strip(".,?!")) > 3
        }

        scored_memories = []

        for memory in self.get_memories():
            memory_words = {
                word.strip(".,?!").lower()
                for word in memory["content"].split()
            }

            score = len(query_words & memory_words)

            if score > 0:
                scored_memories.append((score, memory))

        scored_memories.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        return [
            memory
            for score, memory in scored_memories
        ]

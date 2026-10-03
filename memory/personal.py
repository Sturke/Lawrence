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
                    "source_type": "TEXT",
                    "confidence": "TEXT",
                    "status": "TEXT",
                }

                for column, column_type in structured_columns.items():
                    if column not in existing_columns:
                        connection.execute(
                            f"ALTER TABLE personal_memories "
                            f"ADD COLUMN {column} {column_type}"
                        )
                connection.execute(
                    """UPDATE personal_memories
                    SET status = ?
                    WHERE status IS NULL""",
                    ("active",),
                )

    def save_memory(
        self,
        *,
        content,
        category=None,
        subject=None,
        value=None,
        created_at=None,
        source_type="direct_user_statement",
        confidence="high",
        status="active"
    ):
        """Save or update an explicitly approved personal memory."""

        now = datetime.now(timezone.utc).isoformat()

        if created_at is None:
            created_at = now

        with closing(sqlite3.connect(self.database_path)) as connection:
            with connection:
                if category is not None and subject is not None:
                    existing = connection.execute(
                        """SELECT id
                           FROM personal_memories
                           WHERE category = ?
                             AND subject = ?
                           ORDER BY id
                           LIMIT 1""",
                        (category, subject),
                    ).fetchone()

                    if existing is not None:
                        memory_id = existing[0]

                        connection.execute(
                            """UPDATE personal_memories
                            SET content = ?,
                                value = ?,
                                updated_at = ?,
                                source_type = ?,
                                confidence = ?,
                                status = ?
                            WHERE id = ?""",
                            (
                                content,
                                value,
                                now,
                                source_type,
                                confidence,
                                status,
                                memory_id,
                            ),
                        )

                        return memory_id

                cursor = connection.execute(
                    """INSERT INTO personal_memories
                       (
                           content,
                           category,
                           subject,
                           value,
                           created_at,
                           updated_at,
                           source_type,
                           confidence,
                           status
                       )
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        content,
                        category,
                        subject,
                        value,
                        created_at,
                        now,
                        source_type,
                        confidence,
                        status
                    ),
                )

                return cursor.lastrowid

    def migrate_legacy_favorites(self):
        """Convert legacy favorite memories to structured memories."""

        memories = self.get_memories()

        legacy_memories = [
            memory
            for memory in memories
            if memory["category"] is None
            and memory["content"].lower().startswith("my favorite ")
            and " is " in memory["content"].lower()
        ]

        for memory in legacy_memories:
            content = memory["content"]
            subject_and_value = content[len("My favorite "):]
            subject, value = subject_and_value.split(" is ", 1)

            subject = subject.strip()
            value = value.rstrip(".").strip()

            with closing(sqlite3.connect(self.database_path)) as connection:
                with connection:
                    connection.execute(
                        "DELETE FROM personal_memories WHERE id = ?",
                        (memory["id"],),
                    )

            self.save_memory(
                content=content,
                category="preference",
                subject=subject,
                value=value,
                created_at=memory["created_at"],
                source_type=memory.get("source_type"),
                confidence=memory.get("confidence"),
                status=memory.get("status") or "active",
            )

        return len(legacy_memories)

    def get_memories(self):
        """Return all personal memories in the order they were stored."""
        with closing(sqlite3.connect(self.database_path)) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """SELECT id, content, category, subject, value,
                    created_at, updated_at, source_type, confidence, status
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

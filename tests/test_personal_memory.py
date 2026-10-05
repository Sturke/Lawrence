from memory.personal import PersonalMemoryStore


def test_memory_survives_reopening(tmp_path):
    database = tmp_path / "personal.sqlite3"

    store = PersonalMemoryStore(database)
    memory_id = store.save_memory(content="My favorite college is UIUC.")

    assert memory_id == 1

    reopened = PersonalMemoryStore(database)

    assert database.exists()
    memories = reopened.get_memories()

    assert len(memories) == 1
    assert memories[0]["id"] == memory_id
    assert memories[0]["content"] == "My favorite college is UIUC."
    assert "created_at" in memories[0]

def test_memory_can_be_retrieved_after_reopening(tmp_path):
    database = tmp_path / "personal.sqlite3"

    store = PersonalMemoryStore(database)
    store.save_memory(content="My favorite college is UIUC.")

    reopened = PersonalMemoryStore(database)
    memories = reopened.get_memories()

    assert memories[0]["content"] == "My favorite college is UIUC."

def test_memory_can_be_searched(tmp_path):
    database = tmp_path / "personal.sqlite3"

    store = PersonalMemoryStore(database)
    store.save_memory(content="My favorite college is UIUC.")
    store.save_memory(content="My favorite coffee is Sumatra.")

    memories = store.search_memories(query="college")

    assert len(memories) == 1
    assert memories[0]["content"] == "My favorite college is UIUC."

def test_memory_can_find_relevant_memories(tmp_path):
    database = tmp_path / "personal.sqlite3"

    store = PersonalMemoryStore(database)
    store.save_memory(content="My favorite college is UIUC.")
    store.save_memory(content="My favorite coffee is Sumatra.")

    memories = store.find_relevant_memories(
        query="What coffee do I like?"
    )

    assert len(memories) == 1
    assert memories[0]["content"] == "My favorite coffee is Sumatra."

def test_existing_database_is_upgraded_for_structured_memory(tmp_path):
    database = tmp_path / "personal.sqlite3"

    import sqlite3

    connection = sqlite3.connect(database)
    connection.execute("""
        CREATE TABLE personal_memories (
            id INTEGER PRIMARY KEY,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    connection.execute(
        """INSERT INTO personal_memories
           (content, created_at)
           VALUES (?, ?)""",
        ("My favorite coffee is Sumatra.", "2026-01-01T00:00:00+00:00"),
    )
    connection.commit()
    connection.close()

    store = PersonalMemoryStore(database)

    memories = store.get_memories()

    assert len(memories) == 1
    assert memories[0]["content"] == "My favorite coffee is Sumatra."
    assert memories[0]["category"] is None
    assert memories[0]["subject"] is None
    assert memories[0]["value"] is None
    assert memories[0]["updated_at"] is None

def test_structured_memory_can_be_saved(tmp_path):
    database = tmp_path / "personal.sqlite3"

    store = PersonalMemoryStore(database)

    store.save_memory(
        content="My favorite coffee is Sumatra.",
        category="preference",
        subject="coffee",
        value="Sumatra",
    )

    memories = store.get_memories()

    assert len(memories) == 1
    assert memories[0]["content"] == "My favorite coffee is Sumatra."
    assert memories[0]["category"] == "preference"
    assert memories[0]["subject"] == "coffee"
    assert memories[0]["value"] == "Sumatra"
    assert memories[0]["created_at"] is not None
    assert memories[0]["updated_at"] is not None

def test_structured_memory_updates_existing_subject(tmp_path):
    database = tmp_path / "personal.sqlite3"

    store = PersonalMemoryStore(database)

    first_id = store.save_memory(
        content="My favorite coffee is Sumatra.",
        category="preference",
        subject="coffee",
        value="Sumatra",
    )

    second_id = store.save_memory(
        content="My favorite coffee is Ethiopian Yirgacheffe.",
        category="preference",
        subject="coffee",
        value="Ethiopian Yirgacheffe",
    )

    memories = store.get_memories()

    assert len(memories) == 1
    assert second_id == first_id
    assert memories[0]["category"] == "preference"
    assert memories[0]["subject"] == "coffee"
    assert memories[0]["value"] == "Ethiopian Yirgacheffe"
    assert memories[0]["content"] == (
        "My favorite coffee is Ethiopian Yirgacheffe."
    )
    assert memories[0]["updated_at"] is not None

def test_legacy_favorite_memories_can_be_migrated(tmp_path):
    database = tmp_path / "personal.sqlite3"

    store = PersonalMemoryStore(database)

    store.save_memory(content="My favorite college is UIUC.")
    store.save_memory(content="My favorite college is UIUC.")
    store.save_memory(content="My favorite coffee is Sumatra.")

    migrated_count = store.migrate_legacy_favorites()

    memories = store.get_memories()

    assert migrated_count == 3
    assert len(memories) == 2

    college = next(
        memory
        for memory in memories
        if memory["subject"] == "college"
    )

    coffee = next(
        memory
        for memory in memories
        if memory["subject"] == "coffee"
    )

    assert college["category"] == "preference"
    assert college["value"] == "UIUC"

    assert coffee["category"] == "preference"
    assert coffee["value"] == "Sumatra"

def test_legacy_favorite_migration_is_idempotent(tmp_path):
    database = tmp_path / "personal.sqlite3"

    store = PersonalMemoryStore(database)

    store.save_memory(content="My favorite college is UIUC.")
    store.save_memory(content="My favorite coffee is Sumatra.")

    first_count = store.migrate_legacy_favorites()
    memories_after_first_migration = store.get_memories()

    second_count = store.migrate_legacy_favorites()
    memories_after_second_migration = store.get_memories()

    assert first_count == 2
    assert second_count == 0
    assert memories_after_second_migration == memories_after_first_migration

def test_legacy_migration_preserves_created_at(tmp_path):
    database = tmp_path / "personal.sqlite3"

    store = PersonalMemoryStore(database)
    store.save_memory(content="My favorite coffee is Sumatra.")

    original_memory = store.get_memories()[0]
    original_created_at = original_memory["created_at"]

    store.migrate_legacy_favorites()

    migrated_memory = store.get_memories()[0]

    assert migrated_memory["created_at"] == original_created_at

def test_new_memory_has_default_provenance(tmp_path):
    database = tmp_path / "personal.sqlite3"

    store = PersonalMemoryStore(database)

    store.save_memory(
        content="My favorite coffee is Sumatra.",
        category="preference",
        subject="coffee",
        value="Sumatra",
    )

    memories = store.get_memories()

    assert len(memories) == 1
    assert memories[0]["source_type"] == "direct_user_statement"
    assert memories[0]["confidence"] == "high"
    assert memories[0]["status"] == "active"

def test_memory_can_store_explicit_provenance(tmp_path):
    database = tmp_path / "personal.sqlite3"

    store = PersonalMemoryStore(database)

    store.save_memory(
        content="Burke may prefer dark roast coffee.",
        category="preference",
        subject="coffee",
        value="dark roast",
        source_type="inference",
        confidence="low",
        status="active",
    )

    memories = store.get_memories()

    assert len(memories) == 1
    assert memories[0]["source_type"] == "inference"
    assert memories[0]["confidence"] == "low"
    assert memories[0]["status"] == "active"

def test_updating_memory_updates_provenance(tmp_path):
    database = tmp_path / "personal.sqlite3"

    store = PersonalMemoryStore(database)

    memory_id = store.save_memory(
        content="My favorite coffee is Sumatra.",
        category="preference",
        subject="coffee",
        value="Sumatra",
        source_type="inference",
        confidence="low",
        status="active",
    )

    updated_memory_id = store.save_memory(
        content="My favorite coffee is Ethiopian Yirgacheffe.",
        category="preference",
        subject="coffee",
        value="Ethiopian Yirgacheffe",
        source_type="direct_user_statement",
        confidence="high",
        status="active",
    )

    memories = store.get_memories()

    assert updated_memory_id == memory_id
    assert len(memories) == 1
    assert memories[0]["value"] == "Ethiopian Yirgacheffe"
    assert memories[0]["source_type"] == "direct_user_statement"
    assert memories[0]["confidence"] == "high"
    assert memories[0]["status"] == "active"

def test_existing_memory_gets_active_status_during_schema_migration(tmp_path):
    import sqlite3

    database = tmp_path / "personal.sqlite3"

    connection = sqlite3.connect(database)

    connection.execute("""
        CREATE TABLE personal_memories (
            id INTEGER PRIMARY KEY,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            category TEXT,
            subject TEXT,
            value TEXT,
            updated_at TEXT
        )
    """)

    connection.execute(
        """INSERT INTO personal_memories
           (
               content,
               created_at,
               category,
               subject,
               value,
               updated_at
           )
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            "My favorite coffee is Sumatra.",
            "2026-10-03T16:45:50+00:00",
            "preference",
            "coffee",
            "Sumatra",
            "2026-10-03T20:15:32+00:00",
        ),
    )

    connection.commit()
    connection.close()

    store = PersonalMemoryStore(database)

    memories = store.get_memories()

    assert len(memories) == 1
    assert memories[0]["content"] == "My favorite coffee is Sumatra."
    assert memories[0]["source_type"] is None
    assert memories[0]["confidence"] is None
    assert memories[0]["status"] == "active"

def test_legacy_favorite_migration_preserves_unknown_provenance(tmp_path):
    database = tmp_path / "personal.sqlite3"
    store = PersonalMemoryStore(database)

    store.save_memory(
        content="My favorite tea is Earl Grey.",
        source_type=None,
        confidence=None,
        status="active",
    )

    store.migrate_legacy_favorites()

    memories = store.get_memories()

    assert len(memories) == 1
    assert memories[0]["category"] == "preference"
    assert memories[0]["subject"] == "tea"
    assert memories[0]["value"] == "Earl Grey"
    assert memories[0]["source_type"] is None
    assert memories[0]["confidence"] is None
    assert memories[0]["status"] == "active"

def test_relevant_memory_uses_structured_fields(tmp_path):
    database = tmp_path / "personal.sqlite3"
    store = PersonalMemoryStore(database)

    store.save_memory(
        content="Sumatra is my usual choice.",
        category="preference",
        subject="coffee",
        value="Sumatra",
    )

    store.save_memory(
        content="I enjoy working with Python.",
        category="preference",
        subject="programming language",
        value="Python",
    )

    memories = store.find_relevant_memories(
        query="What coffee do I like?"
    )

    assert len(memories) == 1
    assert memories[0]["subject"] == "coffee"
    assert memories[0]["value"] == "Sumatra"

def test_relevant_memory_ignores_inactive_memories(tmp_path):
    database = tmp_path / "personal.sqlite3"
    store = PersonalMemoryStore(database)

    store.save_memory(
        content="My favorite coffee used to be Sumatra.",
        category="former_preference",
        subject="coffee",
        value="Sumatra",
        status="inactive",
    )

    store.save_memory(
        content="My favorite college is UIUC.",
        category="preference",
        subject="college",
        value="UIUC",
        status="active",
    )

    memories = store.find_relevant_memories(
        query="What coffee do I like?"
    )

    assert memories == []

def test_relevant_memory_prefers_stronger_provenance(tmp_path):
    database = tmp_path / "personal.sqlite3"
    store = PersonalMemoryStore(database)

    store.save_memory(
        content="Burke may prefer dark roast coffee.",
        category="preference",
        subject="coffee style",
        value="dark roast",
        source_type="inference",
        confidence="low",
    )

    store.save_memory(
        content="My favorite coffee is Sumatra.",
        category="preference",
        subject="coffee",
        value="Sumatra",
        source_type="direct_user_statement",
        confidence="high",
    )

    memories = store.find_relevant_memories(
        query="What coffee do I like?"
    )

    assert len(memories) == 2
    assert memories[0]["value"] == "Sumatra"
    assert memories[0]["source_type"] == "direct_user_statement"
    assert memories[0]["confidence"] == "high"

def test_relevant_memory_prefers_subject_match_over_content_match(tmp_path):
    database = tmp_path / "personal.sqlite3"
    store = PersonalMemoryStore(database)


    store.save_memory(
        content="I bought coffee while shopping for a keyboard.",
        category="activity",
        subject="keyboard shopping",
        value="bought supplies",
    )


    store.save_memory(
        content="Sumatra is my usual choice.",
        category="preference",
        subject="coffee",
        value="Sumatra",
    )


    memories = store.find_relevant_memories(
        query="What coffee do I like?"
    )

    assert len(memories) == 2
    assert memories[0]["subject"] == "coffee"
    assert memories[0]["value"] == "Sumatra"
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
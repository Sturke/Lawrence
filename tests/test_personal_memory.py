import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "memory"))

from personal import PersonalMemoryStore


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
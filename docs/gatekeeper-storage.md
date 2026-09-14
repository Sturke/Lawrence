# Gatekeeper message persistence

`memory/gatekeeper.py` provides a standalone `MessageStore` using Python's
standard-library SQLite support. It is separate from Brain and Conversation;
the current interaction loop is unchanged.

The `gatekeeper_messages` table stores a local integer primary key (`id`) and
four required text fields: `sender`, `subject`, `body`, and `received_at`.
Empty subjects and bodies are allowed. Supply `received_at` as an ISO 8601
timestamp with timezone; this layer preserves it without parsing or validation.

On macOS, use `~/Library/Application Support/Butler/gatekeeper.sqlite3` for
persistent local storage outside the repository. The `~` denotes your home
directory. The example below expands it and creates the Butler directory
before opening the database; `MessageStore` itself does not create directories.

```python
from pathlib import Path

from memory.gatekeeper import MessageStore

database_path = Path("~/Library/Application Support/Butler/gatekeeper.sqlite3").expanduser()
database_path.parent.mkdir(parents=True, exist_ok=True)
store = MessageStore(database_path)
message_id = store.save_message(
    sender="sender@example.com",
    subject="Example",
    body="A message for Gatekeeper.",
    received_at="2026-09-13T23:30:00Z",
)
message = store.get_message(message_id)
```

Initialization creates the table if needed and preserves existing messages.
Saves commit before returning the new ID. Lookup returns a dictionary or `None`.
Connections close after each operation. SQL values use bound parameters.
Repeated saves create separate records; provider IDs and deduplication can be
added when an email ingestion adapter is introduced.

The caller selects the database location. Message contents are stored as plain
text in the SQLite file; keep real message databases outside version control.
This step does not connect to email, classify messages, or take actions.

Run the full suite from the repository root with `.venv/bin/python -m pytest -q`.
Storage tests use temporary database files and check persistence after reopening,
exact content retrieval, missing IDs, required fields, and recovery after a
rejected insert.

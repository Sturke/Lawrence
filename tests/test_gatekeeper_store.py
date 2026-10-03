import sqlite3

import pytest

from memory.gatekeeper import MessageStore


def test_message_survives_reopening(tmp_path):
    database = tmp_path / "gatekeeper.sqlite3"
    store = MessageStore(database)
    message = {
        "sender": "sender@example.com",
        "subject": "Burke's update — hello",
        "body": "First line\n'); DROP TABLE gatekeeper_messages; --",
        "received_at": "2026-09-13T18:30:00-05:00",
    }
    message_id = store.save_message(**message)

    reopened = MessageStore(database)
    assert reopened.get_message(message_id) == {"id": message_id, **message}
    second_id = reopened.save_message(**{**message, "subject": "", "body": ""})
    assert second_id != message_id
    assert reopened.get_message(second_id) == {
        **message, "id": second_id, "subject": "", "body": ""
    }
    assert reopened.get_message(message_id) == {"id": message_id, **message}


def test_unknown_message_returns_none(tmp_path):
    store = MessageStore(tmp_path / "gatekeeper.sqlite3")
    assert store.get_message(999) is None


@pytest.mark.parametrize("field", ["sender", "subject", "body", "received_at"])
def test_required_fields_and_recovery(tmp_path, field):
    store = MessageStore(tmp_path / "gatekeeper.sqlite3")
    message = dict(sender="sender@example.com", subject="", body="",
                   received_at="2026-09-13T23:30:00Z")
    with pytest.raises(sqlite3.IntegrityError):
        store.save_message(**{**message, field: None})
    message_id = store.save_message(**message)
    assert store.get_message(message_id) == {"id": message_id, **message}


@pytest.mark.parametrize("path", ["", ":memory:"])
def test_rejects_nonpersistent_database(path):
    with pytest.raises(ValueError, match="persistent database file path"):
        MessageStore(path)

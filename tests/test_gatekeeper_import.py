import sys
from email.message import EmailMessage
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from memory.gatekeeper import MessageStore
from tools.gatekeeper_import import import_email, main, read_email


SAMPLE = Path(__file__).parent / "fixtures" / "sample.eml"


def test_sample_persists_and_repeated_imports_create_rows(tmp_path):
    database = tmp_path / "messages.sqlite3"
    store = MessageStore(database)
    first = import_email(SAMPLE, store)
    second = import_email(SAMPLE, store)
    assert first != second
    saved = MessageStore(database).get_message(first)
    assert saved == {
        "id": first,
        "sender": "Alex Example <alex@example.com>",
        "subject": "Sample garden club reminder",
        "body": "Hello Taylor,\n\nThis is a fictional reminder for Saturday's garden club meeting at 10 AM.\nPlease bring your notebook.\n\nAlex\n",
        "received_at": "2026-09-13T18:30:00-05:00",
    }


def test_multipart_decodes_text_and_ignores_html_and_attachment(tmp_path):
    message = EmailMessage()
    message["From"] = "Alex Example <alex@example.com>"
    message["Subject"] = "Café update"
    message["Date"] = "Sun, 13 Sep 2026 18:30:00 -0500"
    message.set_content("Hello café!", charset="utf-8", cte="base64")
    message.add_alternative("<p>HTML alternative</p>", subtype="html")
    message.add_attachment("Attachment text", filename="notes.txt")
    path = tmp_path / "multipart.eml"
    path.write_bytes(message.as_bytes())
    result = read_email(path)
    assert result["body"] == "Hello café!\n"
    assert result["subject"] == "Café update"


def test_missing_subject_and_empty_body_are_allowed(tmp_path):
    path = tmp_path / "empty.eml"
    path.write_bytes(b"From: alex@example.com\nDate: Sun, 13 Sep 2026 18:30:00 +0000\n\n")
    result = read_email(path)
    assert result["subject"] == ""
    assert result["body"] == ""


@pytest.mark.parametrize("content, reason", [
    ("Date: Sun, 13 Sep 2026 18:30:00 +0000\n\nHello", "From header"),
    ("From: alex@example.com\n\nHello", "valid Date"),
    ("From: alex@example.com\nDate: yesterday\n\nHello", "valid Date"),
    ("From: alex@example.com\nDate: Sun, 13 Sep 2026 18:30:00 -0000\n\nHello", "known timezone"),
    ("From: alex@example.com\nDate: Sun, 13 Sep 2026 18:30:00 +0000\nContent-Type: text/html\n\n<p>Hello</p>", "plain-text body"),
])
def test_invalid_email_does_not_store_a_row(tmp_path, content, reason):
    path = tmp_path / "invalid.eml"
    path.write_text(content)
    store = MessageStore(tmp_path / "messages.sqlite3")
    with pytest.raises(ValueError, match=reason):
        import_email(path, store)
    assert store.get_message(1) is None


def test_command_creates_directory_and_reports_id(tmp_path, capsys):
    database = tmp_path / "Butler" / "messages.sqlite3"
    main([str(SAMPLE), "--database", str(database)])
    assert f"Stored message 1 in {database}" in capsys.readouterr().out
    assert MessageStore(database).get_message(1)["subject"] == "Sample garden club reminder"


def test_missing_file_reports_error_without_creating_database(tmp_path, capsys):
    database = tmp_path / "Butler" / "messages.sqlite3"
    with pytest.raises(SystemExit) as error:
        main([str(tmp_path / "missing.eml"), "--database", str(database)])
    assert error.value.code == 1
    assert "Import failed:" in capsys.readouterr().err
    assert not database.parent.exists()

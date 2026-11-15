import json

from memory.gatekeeper import MessageStore
from tools.gatekeeper_import import main


def assess(tmp_path, capsys, subject, body):
    source = tmp_path / "saved.eml"
    source.write_text(
        "From: Sender <sender@example.com>\n"
        "Date: Sat, 14 Nov 2026 10:00:00 -0600\n"
        f"Subject: {subject}\n\n{body}",
        encoding="utf-8",
    )
    database = tmp_path / "messages.sqlite3"
    main([str(source), "--database", str(database), "--assess"])
    record = json.loads(capsys.readouterr().out)
    assert record["version"] == "0.1"
    assert MessageStore(database).get_message(record["message_id"])["body"] == body
    assert record["confidence"] == "low"
    assert record["reason"]
    assert record["limitations"]
    return record


def test_assessment_reports_each_signal_with_exact_local_evidence(tmp_path, capsys):
    record = assess(tmp_path, capsys, "Verify Your Password", "Buy gift cards.\n")
    assert record["disposition"] == "review_required"
    findings = record["findings"]
    assert [item["category"] for item in findings] == [
        "credential_request", "payment_request",
    ]
    for item, field, excerpt in zip(
        findings, ("subject", "body"), ("Verify Your Password", "gift cards"),
    ):
        assert item["confidence"] == "low"
        assert item["reason"]
        assert item["evidence"] == {
            "field": field,
            "excerpt": excerpt,
            "source_type": "local_email",
            "verification_status": "unverified",
        }


def test_no_supported_signal_is_inconclusive(tmp_path, capsys):
    record = assess(tmp_path, capsys, "Meeting notes", "See you tomorrow.\n")
    assert record["disposition"] == "inconclusive"
    assert record["findings"] == []

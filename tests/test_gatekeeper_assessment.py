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
    assert record["version"] == "0.2"
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

def test_reply_to_domain_mismatch_requires_review(tmp_path, capsys):
    source = tmp_path / "reply-to-mismatch.eml"
    source.write_text(
        "From: Notices <notices@example.com>\n"
        "Reply-To: Support <support@example.org>\n"
        "Date: Sat, 14 Nov 2026 10:00:00 -0600\n"
        "Subject: Meeting notes\n"
        "\n"
        "See you tomorrow.\n",
        encoding="utf-8",
    )

    database = tmp_path / "messages.sqlite3"
    main([str(source), "--database", str(database), "--assess"])
    record = json.loads(capsys.readouterr().out)

    assert record["disposition"] == "review_required"
    finding, = record["findings"]
    assert finding["category"] == "reply_to_domain_mismatch"
    assert finding["confidence"] == "low"
    assert finding["evidence"]["from_domain"] == "example.com"
    assert finding["evidence"]["reply_to_domain"] == "example.org"

def test_matching_reply_to_domain_does_not_require_review(tmp_path, capsys):
    source = tmp_path / "reply-to-mismatch.eml"
    source.write_text(
        "From: Notices <notices@example.com>\n"
        "Reply-To: Support <support@EXAMPLE.COM>\n"
        "Date: Sat, 14 Nov 2026 10:00:00 -0600\n"
        "Subject: Meeting notes\n"
        "\n"
        "See you tomorrow.\n",
        encoding="utf-8",
    )

    database = tmp_path / "messages.sqlite3"
    main([str(source), "--database", str(database), "--assess"])
    record = json.loads(capsys.readouterr().out)

    assert record["disposition"] == "inconclusive"
    assert record["version"] == "0.2"
    assert record["findings"] == []
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
    assert record["version"] == "0.6"
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
    assert record["recognized"] == []

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
    assert record["version"] == "0.6"
    assert record["checks"]["reply_to_domains"] == {"status": "compared"}
    assert record["findings"] == []

def test_link_domain_mismatch_requires_review(tmp_path, capsys):
    from email.message import EmailMessage

    email = EmailMessage()
    email["From"] = "Notices <notices@example.com>"
    email["Date"] = "Sat, 14 Nov 2026 10:00:00 -0600"
    email["Subject"] = "Meeting notes"
    email.set_content("See you tomorrow.")
    email.add_alternative(
        '<p>Meeting details at <a href="https://example.org/">example.com</a>.</p>',
        subtype="html",
    )

    source = tmp_path / "link-mismatch.eml"
    source.write_bytes(email.as_bytes())
    database = tmp_path / "messages.sqlite3"

    main([str(source), "--database", str(database), "--assess"])
    record = json.loads(capsys.readouterr().out)

    assert record["disposition"] == "review_required"
    assert record["checks"]["html_link_domains"]["links_compared"] == 1
    (finding,) = record["findings"]
    assert finding["category"] == "link_domain_mismatch"
    assert finding["confidence"] == "low"
    assert finding["evidence"]["displayed_domain"] == "example.com"
    assert finding["evidence"]["destination_domain"] == "example.org"

def test_matching_link_domain_does_not_require_review(tmp_path, capsys):
    from email.message import EmailMessage

    email = EmailMessage()
    email["From"] = "Notices <notices@example.com>"
    email["Date"] = "Sat, 14 Nov 2026 10:00:00 -0600"
    email["Subject"] = "Meeting notes"
    email.set_content("See you tomorrow.")
    email.add_alternative(
        '<p>Meeting details at <a href="https://example.com/">example.com</a>.</p>',
        subtype="html",
    )

    source = tmp_path / "link-mismatch.eml"
    source.write_bytes(email.as_bytes())
    database = tmp_path / "messages.sqlite3"

    main([str(source), "--database", str(database), "--assess"])
    record = json.loads(capsys.readouterr().out)

    assert record["disposition"] == "inconclusive"
    assert record["findings"] == []
    assert record["checks"]["html_link_domains"] == {
        "status": "compared",
        "links_compared": 1,
    }


def test_zero_link_comparisons_explain_why():
    from verification.email_assessment import assess_email

    message = {"subject": "Meeting notes", "body": "See you tomorrow."}
    without_html = assess_email(1, message)
    with_html = assess_email(
        1, message, html_body='<a href="https://example.com/">Meeting notes</a>'
    )

    assert without_html["checks"]["html_link_domains"] == {
        "status": "skipped",
        "reason": "html_body_unavailable",
        "links_compared": 0,
    }
    assert with_html["checks"]["html_link_domains"] == {
        "status": "skipped",
        "reason": "no_eligible_links",
        "links_compared": 0,
    }
    assert without_html["checks"]["reply_to_domains"] == {
        "status": "skipped",
        "reason": "from_or_reply_to_domain_unavailable",
    }


def test_recognizes_account_sign_in_notice_from_subject(tmp_path, capsys):
    subject = "Your Example Account was used to sign in to Example Cloud"
    record = assess(tmp_path, capsys, subject, "See account activity.")

    assert record["recognized"] == [{
        "category": "account_sign_in_notice",
        "details": {"service": "Example Cloud"},
        "evidence": {
            "field": "subject",
            "excerpt": subject,
            "source_type": "local_email",
            "verification_status": "unverified",
        },
    }]
    assert record["disposition"] == "inconclusive"
    assert record["findings"] == []


def test_recognized_notice_can_still_require_review(tmp_path, capsys):
    record = assess(tmp_path, capsys, "New sign-in to your account", "Verify your password.")

    assert record["recognized"][0]["category"] == "account_sign_in_notice"
    assert record["recognized"][0]["details"] == {}
    assert record["disposition"] == "review_required"
    assert record["findings"][0]["category"] == "credential_request"


def test_sign_in_notice_extracts_explicit_method(tmp_path, capsys):
    subject = "Your Example Account was used to sign in to Example Cloud via a web browser."
    record = assess(tmp_path, capsys, subject, "See account activity.")

    (notice,) = record["recognized"]
    assert notice["details"] == {
        "service": "Example Cloud",
        "sign_in_method": "a web browser",
    }
    assert notice["evidence"]["excerpt"] == subject
    assert notice["evidence"]["verification_status"] == "unverified"

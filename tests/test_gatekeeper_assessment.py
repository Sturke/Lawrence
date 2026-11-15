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
    assert record["version"] == "1.0"
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
    assert record["version"] == "1.0"
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


def test_recognizes_password_reset_request_from_subject(tmp_path, capsys):
    subject = "Password reset requested"
    record = assess(tmp_path, capsys, subject, "See account activity.")

    assert record["recognized"] == [{
        "category": "password_reset_notice",
        "details": {},
        "evidence": {
            "field": "subject",
            "excerpt": subject,
            "source_type": "local_email",
            "verification_status": "unverified",
        },
    }]
    assert record["disposition"] == "inconclusive"


def test_routine_password_message_is_not_recognized(tmp_path, capsys):
    record = assess(tmp_path, capsys, "Password manager tips", "Use unique passwords.")

    assert record["recognized"] == []


def test_password_reset_notice_can_still_require_review(tmp_path, capsys):
    record = assess(tmp_path, capsys, "Reset your password", "Verify your password.")

    assert record["recognized"][0]["category"] == "password_reset_notice"
    assert record["disposition"] == "review_required"
    assert record["findings"][0]["category"] == "credential_request"


def test_recognizes_password_change_separately_from_reset(tmp_path, capsys):
    subject = "Your password was changed."
    record = assess(tmp_path, capsys, subject, "See account activity.")

    (notice,) = record["recognized"]
    assert notice["category"] == "password_change_notice"
    assert notice["evidence"]["excerpt"] == subject
    assert notice["evidence"]["verification_status"] == "unverified"
    assert record["disposition"] == "inconclusive"
    assert record["findings"] == []


def test_listed_sender_claim_remains_unverified(tmp_path, capsys):
    source = tmp_path / "sender.eml"
    source.write_text(
        "From: Notices <notices@example.com>\n"
        "Authentication-Results: mx.example.net; dmarc=pass header.from=example.com\n"
        "Date: Sat, 14 Nov 2026 10:00:00 -0600\n"
        "Subject: Meeting notes\n\nVerify your password.\n",
        encoding="utf-8",
    )
    database = tmp_path / "messages.sqlite3"
    for approved, expected_match in (
        ("notices@example.com", True),
        ("other@example.com", False),
    ):
        main([
            str(source), "--database", str(database), "--assess",
            "--approved-sender", approved,
        ])
        record = json.loads(capsys.readouterr().out)
        assert record["sender_trust"] == {
            "claimed_address": "notices@example.com",
            "approved_address_match": expected_match,
            "status": "unverified",
            "reason": "trusted_authentication_unavailable",
        }
        assert record["disposition"] == "review_required"


def test_saved_sender_approval_survives_imports_and_can_be_removed(tmp_path, capsys):
    from tools.gatekeeper_senders import main as manage_senders

    database = ["--database", str(tmp_path / "messages.sqlite3")]
    source = tmp_path / "notice.eml"
    source.write_text(
        "From: Notices <notices@example.com>\n"
        "Date: Sat, 14 Nov 2026 10:00:00 -0600\n"
        "Subject: Meeting notes\n\nSee you tomorrow.\n",
        encoding="utf-8",
    )
    assessment = [str(source), "--assess", *database]
    main(assessment)
    assert not json.loads(capsys.readouterr().out)["sender_trust"]["approved_address_match"]

    manage_senders([*database, "approve", "notices@example.com"])
    capsys.readouterr()
    manage_senders([*database, "list"])
    (approval,) = json.loads(capsys.readouterr().out)
    assert approval["address"] == "notices@example.com"
    assert approval["approved_at"]

    main(assessment)
    record = json.loads(capsys.readouterr().out)
    assert record["message_id"] == 2
    assert record["sender_trust"]["approved_address_match"]
    assert record["sender_trust"]["status"] == "unverified"

    manage_senders([*database, "remove", "notices@example.com"])
    capsys.readouterr()
    main(assessment)
    assert not json.loads(capsys.readouterr().out)["sender_trust"]["approved_address_match"]


def test_opt_in_reports_domain_authentication_separately(tmp_path, capsys, monkeypatch):
    import sys
    from types import SimpleNamespace

    source = tmp_path / "signed.eml"
    raw = (
        b"From: notices@example.com\r\n"
        b"DKIM-Signature: placeholder\r\n"
        b"Date: Sat, 14 Nov 2026 10:00:00 -0600\r\n"
        b"Subject: Meeting notes\r\n\r\nVerify your password.\r\n"
    )
    source.write_bytes(raw)
    calls = []

    class Verifier:
        def __init__(self, message):
            assert message == raw
            self.domain = domain
            self.signature_fields = {b"a": b"rsa-sha256", **fields}

        def verify(self, idx):
            calls.append(idx)
            return valid

    monkeypatch.setitem(sys.modules, "dkim", SimpleNamespace(
        DKIM=Verifier, DKIMException=ValueError,
    ))
    args = [str(source), "--assess", "--database", str(tmp_path / "messages.sqlite3"),
            "--approved-sender", "notices@example.com"]
    main(args)
    assert json.loads(capsys.readouterr().out)["sender_trust"]["status"] == "unverified"
    assert calls == []

    for domain, valid, fields, expected in (
        (b"example.com", True, {}, "authenticated"),
        (b"other.example", True, {}, "unverified"),
        (b"example.com", False, {}, "unverified"),
        (b"example.com", True, {b"l": b"0"}, "unverified"),
    ):
        main([*args, "--verify-dkim"])
        record = json.loads(capsys.readouterr().out)
        assert record["sender_domain_authentication"]["status"] == expected
        assert record["sender_trust"]["approved_address_match"]
        assert record["sender_trust"]["status"] == "unverified"
        assert record["disposition"] == "review_required"


def test_text_report_separates_approval_from_domain_authentication(tmp_path, capsys):
    source = tmp_path / "notice.eml"
    source.write_text(
        "From: Notices <notices@example.com>\n"
        "Date: Sat, 14 Nov 2026 10:00:00 -0600\n"
        "Subject: New sign-in to your account\n\nVerify your password.\n",
        encoding="utf-8",
    )
    main([
        str(source), "--assess", "--format", "text",
        "--database", str(tmp_path / "messages.sqlite3"),
        "--approved-sender", "notices@example.com",
    ])
    output = capsys.readouterr().out
    assert "Message: Account sign-in notice" in output
    assert "Address approval: Matches notices@example.com" in output
    assert "Sender domain: Unverified (DKIM check not requested)" in output
    assert "Message risk: Review required" in output
    assert "Credential request" in output


def test_text_report_shows_each_link_domain_pair(tmp_path, capsys):
    from email.message import EmailMessage

    message = EmailMessage()
    message["From"] = "test@example.com"
    message["Date"] = "Sun, 15 Nov 2026 10:00:00 -0600"
    message.set_content("Meeting information.")
    message.add_alternative(
        '<a href="https://click.example.net/one">example.com</a>'
        '<a href="https://click.example.net/two">example.org</a>',
        subtype="html",
    )
    source = tmp_path / "links.eml"
    source.write_bytes(message.as_bytes())
    main([
        str(source), "--assess", "--format", "text",
        "--database", str(tmp_path / "messages.sqlite3"),
    ])
    output = capsys.readouterr().out
    assert "Message risk: Review required" in output
    assert "Displayed: example.com | Destination: click.example.net" in output
    assert "Displayed: example.org | Destination: click.example.net" in output


def test_recognizes_new_device_sign_in_platform(tmp_path, capsys):
    subject = "New Device Logged In From macOS"
    record = assess(tmp_path, capsys, subject, "See account activity.")

    (notice,) = record["recognized"]
    assert notice["category"] == "account_sign_in_notice"
    assert notice["details"] == {"platform": "macOS"}
    assert notice["evidence"]["excerpt"] == subject
    assert notice["evidence"]["verification_status"] == "unverified"
    assert record["disposition"] == "inconclusive"

    from verification.email_report import format_email_report

    assert "Message: Account sign-in notice (reported platform: macOS)" in format_email_report(record)


def test_recognizes_password_updated_confirmation(tmp_path, capsys):
    subject = "Your password has been updated"
    record = assess(tmp_path, capsys, subject, "Your account settings were updated.")

    (notice,) = record["recognized"]
    assert notice["category"] == "password_change_notice"
    assert notice["evidence"]["excerpt"] == subject
    assert notice["evidence"]["verification_status"] == "unverified"
    assert record["disposition"] == "inconclusive"

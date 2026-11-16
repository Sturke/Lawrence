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

    main([str(source), "--database", str(database), "--assess", "--format", "text"])
    output = capsys.readouterr().out
    assert "Message risk: Review required" in output
    assert "From: example.com | Reply-To: example.org" in output
    assert "Coverage: Reply-To domains differ; HTML links skipped (HTML unavailable)." in output


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
    assert "Source: Plain-text body | Matched: Verify your password" in output


def test_text_report_shows_each_link_domain_pair(tmp_path, capsys):
    from email.message import EmailMessage

    message = EmailMessage()
    message["From"] = "test@example.com"
    message["Date"] = "Sun, 15 Nov 2026 10:00:00 -0600"
    message.set_content("Meeting information.")
    message.add_alternative(
        '<a href="https://click.example.net/one">example.com</a>'
        '<a href="https://click.example.net/two">example.org</a>'
        '<a href="https://mail.example.com/three">example.com</a>'
        '<a href="https://notexample.com/four">example.com</a>',
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
    assert "Destination: mail.example.com (subdomain of displayed domain)" in output
    assert "Destination: notexample.com" in output
    assert output.count("(subdomain of displayed domain)") == 1


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


def test_html_only_assesses_subject_links_and_body_phrases(tmp_path, capsys):
    source = tmp_path / "html-only.eml"
    source.write_text(
        "From: notices@example.com\n"
        "Date: Sun, 15 Nov 2026 10:00:00 -0600\n"
        "Subject: Reset your password\n"
        "Content-Type: text/html; charset=utf-8\n\n"
        '<head><title>Buy gift cards</title></head>'
        '<style>Buy gift cards</style><script>Buy gift cards</script>'
        '<p>Verify your <strong>password</strong>.</p>'
        '<a href="https://example.net/">example.com</a>',
        encoding="utf-8",
    )
    database = tmp_path / "messages.sqlite3"
    main([str(source), "--assess", "--database", str(database)])
    record = json.loads(capsys.readouterr().out)
    assert record["recognized"][0]["category"] == "password_reset_notice"
    phrase, link = record["findings"]
    assert phrase["category"] == "credential_request"
    assert phrase["evidence"]["field"] == "html_body_text"
    assert phrase["evidence"]["excerpt"] == "Verify your password"
    assert link["category"] == "link_domain_mismatch"
    assert record["checks"]["html_body_phrases"] == {"status": "checked"}
    main([str(source), "--assess", "--format", "text", "--database", str(database)])
    output = capsys.readouterr().out
    assert "Source: Extracted HTML text | Matched: Verify your password" in output
    assert record["checks"]["plain_text_body"] == {
        "status": "skipped", "reason": "plain_text_body_unavailable",
    }
    assert MessageStore(database).get_message(record["message_id"])["body"] == ""


def test_recognizes_short_reset_subject(tmp_path, capsys):
    record = assess(tmp_path, capsys, "Reset Password", "See account activity.")
    (notice,) = record["recognized"]
    assert notice["category"] == "password_reset_notice"
    assert notice["evidence"]["excerpt"] == "Reset Password"


def test_recognizes_instagram_password_change_subject(tmp_path, capsys):
    subject = "Your Instagram password has been changed"
    record = assess(tmp_path, capsys, subject, "See account activity.")
    (notice,) = record["recognized"]
    assert notice["category"] == "password_change_notice"
    assert notice["evidence"]["excerpt"] == subject
    assert notice["evidence"]["verification_status"] == "unverified"


def test_password_change_accepts_other_services_but_not_help_subjects():
    from verification.email_assessment import assess_email

    for subject, expected in (
        ("Your Example Cloud password has been changed", ["password_change_notice"]),
        ("How to check whether your password has been changed", []),
        ("Your password has been changed: troubleshooting tips", []),
    ):
        record = assess_email(1, {"subject": subject, "body": ""})
        assert [notice["category"] for notice in record["recognized"]] == expected


def test_text_coverage_distinguishes_matching_domains_and_links():
    from verification.email_assessment import assess_email
    from verification.email_report import format_email_report

    message = {"subject": "Meeting notes", "body": ""}
    record = assess_email(
        1, message, from_domain="example.com", reply_to_domain="example.com",
        html_body='<a href="https://example.com/">example.com</a>',
    )
    assert "Coverage: Reply-To domains match; HTML links compared: 1." in format_email_report(record)

    record = assess_email(1, message, html_body="<p>No links here.</p>")
    assert (
        "Coverage: Reply-To comparison skipped (usable domains unavailable); "
        "HTML links skipped (no eligible links)."
    ) in format_email_report(record)


def test_folder_assessment_continues_after_invalid_email(tmp_path, capsys):
    folder = tmp_path / "mail"
    folder.mkdir()
    headers = "From: test@example.com\nDate: Sun, 15 Nov 2026 10:00:00 +0000\n"
    (folder / "01.eml").write_text(headers + "Subject: Reset Password\n\nHello.")
    (folder / "02.eml").write_text("Invalid email")
    (folder / "03.EML").write_text(headers + "Subject: Notice\n\nVerify your password.")
    (folder / "notes.txt").write_text("Not email.")
    main(["--folder", str(folder), "--assess", "--database", str(tmp_path / "batch.db")])
    batch = json.loads(capsys.readouterr().out)
    first, failed, last = batch["results"]
    assert first["assessment"]["recognized"][0]["category"] == "password_reset_notice"
    assert failed["file"] == "02.eml" and "error" in failed
    assert last["assessment"]["disposition"] == "review_required"
    assert batch["summary"] == {"assessed": 2, "review_required": 1, "import_failures": 1}

    main([
        "--folder", str(folder), "--assess", "--format", "text", "--review-only",
        "--database", str(tmp_path / "filtered.db"),
    ])
    output = capsys.readouterr().out
    assert "01.eml" not in output
    assert "02.eml" in output and "Import failed:" in output
    assert "03.EML" in output and "Review required" in output
    assert "Batch summary: 2 assessed · 1 require review · 1 import failures" in output


def test_review_mark_is_specific_to_saved_message_and_finding(tmp_path, capsys):
    folder = tmp_path / "mail"
    folder.mkdir()
    headers = "From: test@example.com\nDate: Sun, 15 Nov 2026 10:00:00 +0000\n"
    for name in ("first", "second"):
        (folder / f"{name}.eml").write_text(
            headers + f"Subject: {name}\n\nVerify your password. Buy gift cards."
        )
    database = ["--database", str(tmp_path / "review.db")]
    batch = ["--folder", str(folder), "--assess", *database]
    main(batch)
    first, second = json.loads(capsys.readouterr().out)["results"]
    findings = first["assessment"]["findings"]
    assert findings[0]["review_id"] != second["assessment"]["findings"][0]["review_id"]
    main(["--mark-reviewed", findings[0]["review_id"], *database])
    capsys.readouterr()
    main([*batch, "--format", "text", "--review-only"])
    output = capsys.readouterr().out
    assert '"first.eml"' in output and output.count("Credential request:") == 1
    main(["--mark-reviewed", findings[1]["review_id"], *database])
    capsys.readouterr()
    main([*batch, "--format", "text", "--review-only"])
    output = capsys.readouterr().out
    assert '"first.eml"' not in output and '"second.eml"' in output
    main(batch)
    first, second = json.loads(capsys.readouterr().out)["results"]
    assert first["assessment"]["disposition"] == "review_required"
    assert all(f["reviewed_at"] for f in first["assessment"]["findings"])
    assert all(f["reviewed_at"] is None for f in second["assessment"]["findings"])
    main(["--reopen-review", findings[0]["review_id"], *database])
    capsys.readouterr()
    main([*batch, "--format", "text", "--review-only"])
    output = capsys.readouterr().out
    assert '"first.eml"' in output and output.count("Credential request:") == 2


def test_saved_review_queue_works_after_original_is_removed(tmp_path, capsys):
    source = tmp_path / "notice.eml"
    source.write_text(
        "From: test@example.com\nDate: Sun, 15 Nov 2026 10:00:00 +0000\n"
        "Subject: Notice\n\nVerify your password."
    )
    database = ["--database", str(tmp_path / "review.db")]
    for _ in range(2):
        main([str(source), "--assess", *database])
        assessment = json.loads(capsys.readouterr().out)
    review_id = assessment["findings"][0]["review_id"]
    source.unlink()

    main(["--review-queue", *database])
    (entry,) = json.loads(capsys.readouterr().out)["results"]
    assert entry["file"] == "notice.eml"
    assert entry["assessment"]["message_id"] == 2
    assert entry["assessment"]["findings"][0]["review_id"] == review_id

    main(["--mark-reviewed", review_id, *database])
    capsys.readouterr()
    main(["--review-queue", *database])
    assert json.loads(capsys.readouterr().out)["results"] == []

    main(["--reopen-review", review_id, *database])
    capsys.readouterr()
    main(["--review-queue", "--format", "text", *database])
    output = capsys.readouterr().out
    assert "notice.eml" in output and review_id in output
    assert "Message ID: 2" in output
    assert "Review queue: 1 message with pending findings." in output


def test_mark_message_reviewed_only_updates_selected_snapshot(tmp_path, capsys):
    database = ["--database", str(tmp_path / "review.db")]
    for name in ("first", "second"):
        source = tmp_path / f"{name}.eml"
        source.write_text(
            "From: test@example.com\nDate: Sun, 15 Nov 2026 10:00:00 +0000\n"
            f"Subject: {name}\n\nVerify your password. Buy gift cards."
        )
        main([str(source), "--assess", *database])
        if name == "first":
            first = json.loads(capsys.readouterr().out)
        else:
            capsys.readouterr()

    message_id = str(first["message_id"])
    main(["--mark-message-reviewed", message_id, "--review-note", "Checked locally", *database])
    assert "2 findings marked reviewed." in capsys.readouterr().out
    main(["--mark-message-reviewed", message_id, *database])
    assert "0 findings marked reviewed." in capsys.readouterr().out
    main(["--review-queue", *database])
    (entry,) = json.loads(capsys.readouterr().out)["results"]
    assert entry["file"] == "second.eml"
    assert len(entry["assessment"]["findings"]) == 2

    main(["--reviewed", *database])
    (entry,) = json.loads(capsys.readouterr().out)["results"]
    assert entry["file"] == "first.eml"
    reviewed = entry["assessment"]["findings"]
    assert len(reviewed) == 2 and all(f["reviewed_at"] for f in reviewed)
    assert all(f["review_note"] == "Checked locally" for f in reviewed)
    review_id = reviewed[0]["review_id"]

    main(["--reviewed", "--format", "text", *database])
    output = capsys.readouterr().out
    assert review_id in output and reviewed[0]["reviewed_at"] in output
    assert "second.eml" not in output
    assert output.count("Review note: Checked locally") == 2

    main(["--reopen-review", review_id, *database])
    capsys.readouterr()
    main(["--reviewed", *database])
    (entry,) = json.loads(capsys.readouterr().out)["results"]
    assert len(entry["assessment"]["findings"]) == 1
    assert entry["assessment"]["findings"][0]["review_id"] != review_id
    main(["--review-queue", *database])
    first, second = json.loads(capsys.readouterr().out)["results"]
    assert [f["review_id"] for f in first["assessment"]["findings"]] == [review_id]
    assert second["file"] == "second.eml"


def test_review_history_preserves_notes_across_reopen(tmp_path, capsys):
    source = tmp_path / "notice.eml"
    source.write_text(
        "From: test@example.com\nDate: Sun, 15 Nov 2026 10:00:00 +0000\n"
        "Subject: Notice\n\nVerify your password."
    )
    database = ["--database", str(tmp_path / "review.db")]
    main([str(source), "--assess", *database])
    (finding,) = json.loads(capsys.readouterr().out)["findings"]
    review_id = finding["review_id"]
    main(["--mark-reviewed", review_id, "--review-note", "First review", *database])
    main(["--mark-reviewed", review_id, "--review-note", "Duplicate", *database])
    main(["--reopen-review", review_id, *database])
    main(["--mark-message-reviewed", "1", "--review-note", "Second review", *database])
    capsys.readouterr()
    main(["--review-history", review_id, *database])
    history = json.loads(capsys.readouterr().out)["events"]
    assert [(event["action"], event["note"]) for event in history] == [
        ("reviewed", "First review"), ("reopened", None), ("reviewed", "Second review"),
    ]
    assert all(event["timestamp"].endswith("+00:00") for event in history)

    main(["--message-history", "1", *database])
    message_history = json.loads(capsys.readouterr().out)
    assert message_history["message_id"] == 1
    assert message_history["file"] == "notice.eml"
    (entry,) = message_history["findings"]
    assert entry["review_id"] == review_id
    assert entry["category"] == "credential_request"
    assert entry["events"] == history

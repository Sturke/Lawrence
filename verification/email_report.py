"""Readable terminal output for a Gatekeeper assessment."""


PHRASE_SOURCES = {
    "subject": "Subject",
    "body": "Plain-text body",
    "html_body_text": "Extracted HTML text",
}


def _terminal_text(value):
    """Escape nonprinting characters from message-derived fields."""
    return "".join(char if char.isprintable() else repr(char)[1:-1] for char in value)


def format_email_report(record):
    notices = []
    for notice in record["recognized"]:
        label = notice["category"].replace("_", " ").capitalize()
        if notice["category"] == "account_sign_in_notice":
            label = "Account sign-in notice"
        details = notice["details"]
        if details.get("service"):
            label += f' for {_terminal_text(details["service"])}'
        if details.get("sign_in_method"):
            label += f' via {_terminal_text(details["sign_in_method"])}'
        if details.get("platform"):
            label += f' (reported platform: {_terminal_text(details["platform"])})'
        notices.append(label)

    sender = record["sender_trust"]
    claimed = sender["claimed_address"]
    approval = "Claimed address unavailable"
    if claimed:
        prefix = "Matches" if sender["approved_address_match"] else "No approval for"
        approval = f"{prefix} {_terminal_text(claimed)}"

    authentication = record["sender_domain_authentication"]
    if authentication["status"] == "authenticated":
        domain = _terminal_text(authentication["signing_domain"])
        domain_result = f"{domain} authenticated via DKIM"
    else:
        reason = {
            "dkim_verification_not_requested": "DKIM check not requested",
            "from_domain_unavailable": "From domain unavailable",
            "no_dkim_signature": "No DKIM signature",
            "dkim_verifier_unavailable": "DKIM verifier unavailable",
            "no_valid_matching_signature": "No valid matching DKIM signature",
        }.get(authentication["reason"], "Authentication evidence unavailable")
        domain_result = f"Unverified ({reason})"

    risk = record["disposition"].replace("_", " ").capitalize()
    lines = [
        f"Message: {', '.join(notices) or 'Type not recognized'}",
        f"Address approval: {approval}",
        f"Sender domain: {domain_result}",
        f"Message risk: {risk} — {record['reason']}",
    ]
    for finding in record["findings"]:
        label = finding["category"].replace("_", " ").capitalize()
        lines.append(f"  - {label}: {finding['reason']}")
        if "review_id" in finding:
            timestamp = finding["reviewed_at"]
            state = f"reviewed at {timestamp}" if timestamp else "pending"
            lines.append(f'    Review ID: {finding["review_id"]} ({state})')
            if finding.get("review_note"):
                lines.append(f'    Review note: {_terminal_text(finding["review_note"])}')
        evidence = finding["evidence"]
        if finding["category"] == "link_domain_mismatch":
            displayed = _terminal_text(evidence["displayed_domain"])
            destination = _terminal_text(evidence["destination_domain"])
            if evidence["destination_domain"].endswith("." + evidence["displayed_domain"]):
                destination += " (subdomain of displayed domain)"
            lines.append(f"    Displayed: {displayed} | Destination: {destination}")
        elif finding["category"] in {
            "urgent_action_external_link", "urgent_payment_cloud_page",
            "home_warranty_quote_cloud_page",
        }:
            subject = _terminal_text(evidence["subject"])
            label = _terminal_text(evidence["link_label"])
            sender = _terminal_text(evidence["from_domain"] or "Usable address unavailable")
            destination = _terminal_text(evidence["destination_domain"])
            lines.append(f"    Subject: {subject} | Link label: {label}")
            lines.append(f"    From: {sender} | Destination: {destination}")
        elif finding["category"] == "brand_sender_domain_mismatch":
            brand = _terminal_text(evidence["brand"])
            subject = _terminal_text(evidence["subject"])
            sender = _terminal_text(evidence["from_domain"])
            expected = ", ".join(map(_terminal_text, evidence["expected_domains"]))
            lines.append(f"    Brand: {brand} | Subject: {subject}")
            lines.append(f"    From: {sender} | Expected: {expected}")
        elif finding["category"] == "reply_to_domain_mismatch":
            from_domain = _terminal_text(evidence["from_domain"])
            reply_to_domain = _terminal_text(evidence["reply_to_domain"])
            lines.append(f"    From: {from_domain} | Reply-To: {reply_to_domain}")
        elif evidence.get("field") in PHRASE_SOURCES and "excerpt" in evidence:
            source = PHRASE_SOURCES[evidence["field"]]
            excerpt = _terminal_text(evidence["excerpt"])
            lines.append(f"    Source: {source} | Matched: {excerpt}")
    checks = record["checks"]
    if checks["reply_to_domains"]["status"] == "skipped":
        reply_coverage = "Reply-To comparison skipped (usable domains unavailable)"
    elif any(finding["category"] == "reply_to_domain_mismatch" for finding in record["findings"]):
        reply_coverage = "Reply-To domains differ"
    else:
        reply_coverage = "Reply-To domains match"

    link_check = checks["html_link_domains"]
    if link_check["status"] == "compared":
        link_coverage = f'HTML links compared: {link_check["links_compared"]}'
    else:
        reason = {
            "html_body_unavailable": "HTML unavailable",
            "no_eligible_links": "no eligible links",
        }[link_check["reason"]]
        link_coverage = f"HTML links skipped ({reason})"
    lines.append(f"Coverage: {reply_coverage}; {link_coverage}.")
    plain_text_checked = checks["plain_text_body"]["status"] == "checked"
    html_text_checked = checks["html_body_phrases"]["status"] == "checked"
    if plain_text_checked and html_text_checked:
        lines.append("Coverage: Checked plain-text and extracted HTML for phrases.")
    elif html_text_checked:
        lines.append("Coverage: Checked extracted HTML text (no plain-text body).")
    elif not plain_text_checked:
        lines.append("Coverage: Body phrase check skipped (no usable body text).")
    return "\n".join(lines)

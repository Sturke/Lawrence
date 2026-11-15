"""Deterministic review signals for locally imported plain-text email."""

import re
from html.parser import HTMLParser
from urllib.parse import urlsplit

from verification.evidence import Evidence


RULES = (
    (
        "credential_request",
        re.compile(r"\b(?:verify|enter)\s+your\s+password\b", re.IGNORECASE),
        "Matched wording commonly used to request credentials.",
    ),
    (
        "payment_request",
        re.compile(r"\b(?:wire\s+transfer|gift\s+cards?)\b", re.IGNORECASE),
        "Matched wording associated with payment requests.",
    ),
)

ACCOUNT_SIGN_IN_SUBJECT = re.compile(
    r"(?:your (?:[\w-]+ ){0,5}account was used to sign in to (?P<service>.+?)"
    r"(?: via (?P<sign_in_method>.+?))?"
    r"|new sign[ -]in to your account)[.!]?",
    re.IGNORECASE,
)

PASSWORD_RESET_SUBJECT = re.compile(
    r"(?:password reset request(?:ed)?|reset your password)[.!]?",
    re.IGNORECASE,
)

PASSWORD_CHANGE_SUBJECT = re.compile(
    r"(?:your password (?:was|has been) changed|password changed)[.!]?",
    re.IGNORECASE,
)

NOTICE_SUBJECTS = (
    ("account_sign_in_notice", ACCOUNT_SIGN_IN_SUBJECT),
    ("password_reset_notice", PASSWORD_RESET_SUBJECT),
    ("password_change_notice", PASSWORD_CHANGE_SUBJECT),
)


class LinkDomainParser(HTMLParser):
    domain_pattern = re.compile(
        r"(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,}",
        re.IGNORECASE | re.ASCII,
    )

    def __init__(self):
        super().__init__()
        self.href = None
        self.label_parts = []
        self.links_compared = 0
        self.mismatches = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.href = dict(attrs).get("href")
            self.label_parts = []

    def handle_data(self, data):
        if self.href is not None:
            self.label_parts.append(data)

    def handle_endtag(self, tag):
        if tag != "a" or self.href is None:
            return

        href = self.href
        self.href = None
        displayed_domain = "".join(self.label_parts).strip().lower()
        if not self.domain_pattern.fullmatch(displayed_domain):
            return

        try:
            destination = urlsplit(href)
            destination_domain = destination.hostname
        except ValueError:
            return

        if destination.scheme not in {"http", "https"} or not destination_domain:
            return

        self.links_compared += 1
        if destination_domain.lower() != displayed_domain:
            self.mismatches.append((displayed_domain, destination_domain.lower()))


def assess_email(
    message_id, message, *, from_domain=None, reply_to_domain=None, html_body=None,
    claimed_address=None, approved_senders=(),
):
    """Return a JSON-ready assessment without external verification."""
    findings = []
    for category, pattern, reason in RULES:
        for field in ("subject", "body"):
            match = pattern.search(message[field])
            if match is None:
                continue
            evidence = Evidence(
                claim=f"The imported {field} contains the matched phrase.",
                content=match.group(),
                source_type="local_email",
            )
            findings.append({
                "category": category,
                "confidence": "low",
                "reason": reason,
                "evidence": {
                    "field": field,
                    "excerpt": evidence.content,
                    "source_type": evidence.source_type,
                    "verification_status": evidence.verification_status,
                },
            })
            break

    reply_to_check = {"status": "compared"}
    if not (from_domain and reply_to_domain):
        reply_to_check = {
            "status": "skipped",
            "reason": "from_or_reply_to_domain_unavailable",
        }
    elif from_domain != reply_to_domain:
        findings.append({
            "category": "reply_to_domain_mismatch",
            "confidence": "low",
            "reason": "The Reply-To domain differs from the From domain.",
            "evidence": {
                "from_domain": from_domain,
                "reply_to_domain": reply_to_domain,
                "source_type": "local_email",
                "verification_status": "unverified",
            },
        })

    html_check = {
        "status": "skipped",
        "reason": "html_body_unavailable",
        "links_compared": 0,
    }
    if html_body is not None:
        parser = LinkDomainParser()
        parser.feed(html_body)
        parser.close()
        html_check = {"status": "compared", "links_compared": parser.links_compared}
        if not parser.links_compared:
            html_check.update(status="skipped", reason="no_eligible_links")
        for displayed_domain, destination_domain in parser.mismatches:
            findings.append({
                "category": "link_domain_mismatch",
                "confidence": "low",
                "reason": "The link label and destination show different domains.",
                "evidence": {
                    "displayed_domain": displayed_domain,
                    "destination_domain": destination_domain,
                    "source_type": "local_email",
                    "verification_status": "unverified",
                },
            })

    recognized = []
    for category, pattern in NOTICE_SUBJECTS:
        notice = pattern.fullmatch(message["subject"].strip())
        if notice is None:
            continue
        details = {
            field: value
            for field, value in notice.groupdict().items()
            if value is not None
        }
        recognized.append({
            "category": category,
            "details": details,
            "evidence": {
                "field": "subject",
                "excerpt": message["subject"],
                "source_type": "local_email",
                "verification_status": "unverified",
            },
        })

    return {
        "version": "0.9",
        "sender_trust": {
            "claimed_address": claimed_address,
            "approved_address_match": claimed_address in approved_senders,
            "status": "unverified",
            "reason": (
                "trusted_authentication_unavailable" if claimed_address is not None
                else "claimed_address_unavailable"
            ),
        },
        "recognized": recognized,
        "message_id": message_id,
        "disposition": "review_required" if findings else "inconclusive",
        "confidence": "low",
        "reason": (
            "Review the findings and verify requests through a trusted channel."
            if findings else "No supported risk signals were found. Message risk remains unknown."
        ),
        "findings": findings,
        "checks": {
            "reply_to_domains": reply_to_check,
            "html_link_domains": html_check,
        },
        "limitations": [
            "Phrase matching can miss risks or match benign text.",
            "The assessment checks the subject, plain-text body, and available From and Reply-To domains.",
            "The HTML link check compares domain-only labels with HTTP or HTTPS destination hostnames without opening links.",
            "Sender identity and message claims were not verified.",
        ],
    }

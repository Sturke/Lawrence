"""Deterministic review signals for locally imported plain-text email."""

import re

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


def assess_email(message_id, message, *, from_domain=None, reply_to_domain=None):
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

    if from_domain and reply_to_domain and from_domain != reply_to_domain:
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

    return {
        "version": "0.2",
        "message_id": message_id,
        "disposition": "review_required" if findings else "inconclusive",
        "confidence": "low",
        "reason": (
            "Review the findings and verify requests through a trusted channel."
            if findings else "No supported signals were found. Message risk remains unknown."
        ),
        "findings": findings,
        "limitations": [
            "Phrase matching can miss risks or match benign text.",
            "The assessment checks the subject, plain-text body, and available From and Reply-To domains.",
            "Sender identity and message claims were not verified.",
        ],
    }

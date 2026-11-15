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


def assess_email(message_id, message):
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

    return {
        "version": "0.1",
        "message_id": message_id,
        "disposition": "review_required" if findings else "inconclusive",
        "confidence": "low",
        "reason": (
            "Inspect the quoted phrases and verify requests through a trusted channel."
            if findings else "No supported phrases matched. Message risk remains unknown."
        ),
        "findings": findings,
        "limitations": [
            "Phrase matching can miss risks or match benign text.",
            "Only the subject and plain-text body were evaluated.",
            "Sender identity and message claims were not verified.",
        ],
    }

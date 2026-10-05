import pytest

from verification.evidence import Evidence, VerificationResult


def test_new_evidence_starts_unverified():
    evidence = Evidence(
        claim="The user's Apple account has been suspended.",
        content="An email says the account has been suspended.",
        source_type="email",
    )

    assert evidence.claim == "The user's Apple account has been suspended."
    assert evidence.content == "An email says the account has been suspended."
    assert evidence.source_type == "email"
    assert evidence.verification_status == "unverified"
    assert evidence.confidence is None


def test_evidence_rejects_invalid_verification_status():
    with pytest.raises(ValueError):
        Evidence(
            claim="The user's Apple account has been suspended.",
            content="An email says the account has been suspended.",
            source_type="email",
            verification_status="definitely_true",
        )


def test_verification_result_records_evaluation_separately_from_evidence():
    evidence = Evidence(
        claim="The user's Apple account has been suspended.",
        content="An email says the account has been suspended.",
        source_type="email",
    )

    result = VerificationResult(
        claim=evidence.claim,
        status="unknown",
        confidence="low",
        reason="The email claim has not been independently verified.",
    )

    assert evidence.verification_status == "unverified"

    assert result.claim == evidence.claim
    assert result.status == "unknown"
    assert result.confidence == "low"
    assert result.reason == (
        "The email claim has not been independently verified."
    )


def test_verification_result_rejects_invalid_confidence():
    with pytest.raises(ValueError):
        VerificationResult(
            claim="The user's Apple account has been suspended.",
            status="unknown",
            confidence="absolutely_certain",
            reason="The claim has not been independently verified.",
        )


def test_verification_result_preserves_evidence():
    evidence = Evidence(
        claim="The user's Apple account has been suspended.",
        content="An email says the account has been suspended.",
        source_type="email",
    )

    result = VerificationResult(
        claim=evidence.claim,
        status="unknown",
        confidence="low",
        reason="The email claim has not been independently verified.",
        evidence=[evidence],
    )

    assert result.evidence == [evidence]
    assert result.evidence[0].content == (
        "An email says the account has been suspended."
    )

"""Evidence models for Lawrence's verification system."""


class Evidence:
    """Represent information that may support or dispute a claim."""

    VALID_VERIFICATION_STATUSES = {
        "unverified",
        "supported",
        "disputed",
        "unknown",
    }

    def __init__(
        self,
        *,
        claim,
        content,
        source_type,
        verification_status="unverified",
        confidence=None,
    ):
        if verification_status not in self.VALID_VERIFICATION_STATUSES:
            raise ValueError(
                f"Invalid verification status: {verification_status}"
            )

        self.claim = claim
        self.content = content
        self.source_type = source_type
        self.verification_status = verification_status
        self.confidence = confidence


class VerificationResult:
    """Represent the result of evaluating a claim against evidence."""

    VALID_STATUSES = {
        "supported",
        "disputed",
        "unknown",
    }

    VALID_CONFIDENCE_LEVELS = {
        "low",
        "medium",
        "high",
    }

    def __init__(
        self,
        *,
        claim,
        status,
        confidence,
        reason,
        evidence=None,
    ):
        if status not in self.VALID_STATUSES:
            raise ValueError(
                f"Invalid verification result status: {status}"
            )

        if confidence not in self.VALID_CONFIDENCE_LEVELS:
            raise ValueError(
                f"Invalid verification confidence: {confidence}"
            )

        self.claim = claim
        self.status = status
        self.confidence = confidence
        self.reason = reason
        self.evidence = list(evidence) if evidence is not None else []

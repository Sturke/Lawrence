"""Opt-in verification of a saved message's From domain."""


def authenticate_from_domain(raw, message, from_domain):
    """Verify full-body DKIM signatures against DNS keys."""
    result = {"status": "unverified", "method": "dkim", "from_domain": from_domain}
    if not from_domain:
        return dict(result, reason="from_domain_unavailable")
    signatures = message.get_all("DKIM-Signature", [])
    if not signatures:
        return dict(result, reason="no_dkim_signature")

    try:
        import dkim
    except ImportError:
        return dict(result, reason="dkim_verifier_unavailable")

    for index in range(len(signatures)):
        try:
            verifier = dkim.DKIM(raw)
            if not verifier.verify(idx=index):
                continue
        except (dkim.DKIMException, OSError):
            continue
        fields = verifier.signature_fields
        if b"l" in fields or fields.get(b"a") != b"rsa-sha256":
            continue
        if verifier.domain.lower() == from_domain.encode("utf-8"):
            return dict(result, status="authenticated", signing_domain=from_domain)
    return dict(result, reason="no_valid_matching_signature")

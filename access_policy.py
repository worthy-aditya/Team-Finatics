"""Access policy validation combining consent, domain, and allowlist checks."""

from consent_gate import consent_gate
from domain_verifier import verify_domain


__all__ = ["AccessPolicy", "access_policy", "is_policy_valid"]


def _normalize_domain(value):
    """Normalize a domain-like value before comparison."""
    if value is None:
        return ""
    text = str(value).strip().lower().rstrip(".")
    if not text:
        return ""
    return text.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0].rstrip(".")


def access_policy(consent, expected_domain, domain, allowed_domains, timeout=5, session=None):
    """Return True only when consent, expected domain, and allowlist all match."""
    if consent is None or expected_domain is None or domain is None or not allowed_domains:
        return False

    if not consent_gate(consent, expected_domain):
        return False

    if not verify_domain(domain, expected_domain, timeout=timeout, session=session):
        return False

    normalized_allowed = {_normalize_domain(item) for item in allowed_domains if item is not None}
    if not normalized_allowed:
        return False

    return _normalize_domain(domain) in normalized_allowed


def is_policy_valid(consent, expected_domain, domain, allowed_domains, timeout=5, session=None):
    """Compatibility wrapper for policy validation."""
    return access_policy(consent, expected_domain, domain, allowed_domains, timeout=timeout, session=session)


class AccessPolicy:
    """Simple policy validator."""

    def verify(self, consent, expected_domain, domain, allowed_domains, timeout=5, session=None):
        return access_policy(consent, expected_domain, domain, allowed_domains, timeout=timeout, session=session)

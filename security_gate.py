"""Combined security gate for consent and domain validation."""

from consent_gate import consent_gate
from domain_verifier import verify_domain


__all__ = ["SecurityGate", "security_gate", "is_access_allowed"]


def security_gate(consent, expected_domain, domain, timeout=5, session=None):
    """Return True only when consent and domain checks both pass."""
    if consent is None or expected_domain is None or domain is None:
        return False

    if not consent_gate(consent, expected_domain):
        return False

    return verify_domain(domain, expected_domain, timeout=timeout, session=session)


def is_access_allowed(consent, expected_domain, domain, timeout=5, session=None):
    """Compatibility wrapper for access control checks."""
    return security_gate(consent, expected_domain, domain, timeout=timeout, session=session)


class SecurityGate:
    """Simple security gate validator."""

    def verify(self, consent, expected_domain, domain, timeout=5, session=None):
        return security_gate(consent, expected_domain, domain, timeout=timeout, session=session)

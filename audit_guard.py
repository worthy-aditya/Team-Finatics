"""Audit-aware validation combining session, consent, domain, and allowlist checks."""

from access_policy import access_policy
from domain_verifier import _normalize_domain

__all__ = ["AuditGuard", "audit_guard", "is_audit_valid"]


def _coerce_session(session):
    """Return a usable session-like object or None."""
    if session is None:
        return None
    if hasattr(session, "get"):
        return session
    if isinstance(session, dict):
        return session
    return None


def audit_guard(session, consent, expected_domain, domain, allowed_domains, audit_name, timeout=5):
    """Return True only when the session, consent, domain, allowlist, and audit name all match."""
    if session is None or consent is None or expected_domain is None or domain is None:
        return False

    normalized_session = _coerce_session(session)
    if normalized_session is None:
        return False

    if audit_name is None:
        return False

    if not access_policy(consent, expected_domain, domain, allowed_domains, timeout=timeout, session=normalized_session):
        return False

    try:
        response = normalized_session.get(f"https://{_normalize_domain(domain)}", timeout=timeout)
    except Exception:
        return False

    if response is None:
        return False

    actual_url = getattr(response, "url", None)
    if not actual_url and getattr(response, "request", None):
        actual_url = getattr(response.request, "url", None)
    if not actual_url:
        actual_url = f"https://{_normalize_domain(domain)}"

    return _normalize_domain(actual_url) == _normalize_domain(expected_domain) and str(audit_name).strip().lower() == "audit"


def is_audit_valid(session, consent, expected_domain, domain, allowed_domains, audit_name, timeout=5):
    """Compatibility wrapper for audit validation."""
    return audit_guard(session, consent, expected_domain, domain, allowed_domains, audit_name, timeout=timeout)


class AuditGuard:
    """Simple audit-aware validator."""

    def verify(self, session, consent, expected_domain, domain, allowed_domains, audit_name, timeout=5):
        return audit_guard(session, consent, expected_domain, domain, allowed_domains, audit_name, timeout=timeout)

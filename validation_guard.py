"""Validation-aware checking for session, consent, domain, and allowlist access."""

from access_policy import access_policy
from domain_verifier import _normalize_domain

__all__ = ["ValidationGuard", "validation_guard", "is_validation_valid"]


def _coerce_session(session):
    """Return a usable session-like object or None."""
    if session is None:
        return None
    if hasattr(session, "get"):
        return session
    if isinstance(session, dict):
        return session
    return None


def validation_guard(session, consent, expected_domain, domain, allowed_domains, validation_name, timeout=5):
    """Return True only when the session, consent, domain, allowlist, and validation name all match."""
    if session is None or consent is None or expected_domain is None or domain is None:
        return False

    normalized_session = _coerce_session(session)
    if normalized_session is None:
        return False

    if validation_name is None:
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

    return _normalize_domain(actual_url) == _normalize_domain(expected_domain) and str(validation_name).strip().lower() == "validation"


def is_validation_valid(session, consent, expected_domain, domain, allowed_domains, validation_name, timeout=5):
    """Compatibility wrapper for validation checks."""
    return validation_guard(session, consent, expected_domain, domain, allowed_domains, validation_name, timeout=timeout)


class ValidationGuard:
    """Simple validation-aware validator."""

    def verify(self, session, consent, expected_domain, domain, allowed_domains, validation_name, timeout=5):
        return validation_guard(session, consent, expected_domain, domain, allowed_domains, validation_name, timeout=timeout)

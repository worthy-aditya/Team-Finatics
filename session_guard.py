"""Session-aware access validation combining consent, domain, and allowlist checks."""

from access_policy import access_policy
from domain_verifier import _normalize_domain

__all__ = ["SessionGuard", "session_guard", "is_session_valid"]


def _coerce_session(session):
    """Return a usable session-like object or None."""
    if session is None:
        return None
    if hasattr(session, "get"):
        return session
    if isinstance(session, dict):
        return session
    return None


def session_guard(*args, **kwargs):
    """Validate that a session is authorized for the required domain and allowlist."""
    session = kwargs.pop("session", None)
    consent = kwargs.pop("consent", None)
    expected_domain = kwargs.pop("expected_domain", None)
    domain = kwargs.pop("domain", None)
    allowed_domains = kwargs.pop("allowed_domains", None)

    if len(args) == 5:
        session, consent, expected_domain, domain, allowed_domains = args
    elif len(args) == 4:
        consent, expected_domain, domain, allowed_domains = args
    elif len(args) == 3:
        expected_domain, domain, allowed_domains = args
    elif len(args) == 2:
        domain, allowed_domains = args

    if session is None and isinstance(kwargs.get("client"), (dict, object)):
        session = kwargs.get("client")

    if session is None and isinstance(consent, (dict, object)) and hasattr(consent, "get"):
        session = consent
        consent = kwargs.get("consent")

    if consent is None and "consent" in kwargs:
        consent = kwargs["consent"]

    if allowed_domains is None:
        allowed_domains = kwargs.get("allowlist") or kwargs.get("allowed") or []

    normalized_session = _coerce_session(session)
    if normalized_session is None:
        return False

    if consent is None or expected_domain is None or domain is None:
        return False

    base_valid = access_policy(consent, expected_domain, domain, allowed_domains, timeout=kwargs.get("timeout", 5), session=normalized_session)
    if not base_valid:
        return False

    try:
        response = normalized_session.get(f"https://{_normalize_domain(domain)}", timeout=kwargs.get("timeout", 5))
    except Exception:
        return False

    if response is None:
        return False

    actual_url = getattr(response, "url", None)
    if not actual_url and getattr(response, "request", None):
        actual_url = getattr(response.request, "url", None)
    if not actual_url:
        actual_url = f"https://{_normalize_domain(domain)}"

    return _normalize_domain(actual_url) == _normalize_domain(expected_domain)


def is_session_valid(*args, **kwargs):
    """Compatibility wrapper for session validation."""
    return session_guard(*args, **kwargs)


class SessionGuard:
    """Simple session-aware validation guard."""

    def verify(self, *args, **kwargs):
        return session_guard(*args, **kwargs)

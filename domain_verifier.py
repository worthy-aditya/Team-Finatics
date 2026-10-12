"""Domain verification helpers for consent-gated checks."""

from urllib.parse import urlsplit

import requests


def _normalize_domain(value):
    """Normalize a domain-like value before comparison."""
    if value is None:
        return ""

    candidate = str(value).strip().lower().rstrip(".")
    if not candidate:
        return ""

    if "://" in candidate or candidate.startswith("//"):
        parsed = urlsplit(candidate if "://" in candidate else f"//{candidate}")
        if parsed.hostname:
            candidate = parsed.hostname
    else:
        candidate = candidate.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0]
        if ":" in candidate:
            host_part, port = candidate.rsplit(":", 1)
            if port.isdigit():
                candidate = host_part

    return candidate.rstrip(".")


def verify_domain(domain, expected_domain, timeout=5, session=None):
    """Return True when a reachable domain resolves to the expected hostname."""
    if domain is None or expected_domain is None:
        return False

    target = _normalize_domain(domain)
    expected = _normalize_domain(expected_domain)

    if not target or not expected:
        return False

    if target != expected:
        return False

    client = session or requests
    try:
        response = client.get(f"https://{target}", timeout=timeout)
    except Exception:
        return False

    if response is None:
        return False

    actual_url = getattr(response, "url", None)
    if not actual_url and getattr(response, "request", None):
        actual_url = getattr(response.request, "url", None)

    if not actual_url:
        actual_url = f"https://{target}"

    return _normalize_domain(actual_url) == expected


def is_domain_verified(domain, expected_domain, timeout=5, session=None):
    """Compatibility wrapper for domain verification."""
    return verify_domain(domain, expected_domain, timeout=timeout, session=session)


class DomainVerifier:
    """Simple domain verification validator."""

    def verify(self, domain, expected_domain, timeout=5, session=None):
        return verify_domain(domain, expected_domain, timeout=timeout, session=session)

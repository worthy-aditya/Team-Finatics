"""Consent gate validation for a single expected domain."""

from urllib.parse import urlsplit


def _normalize_domain(value):
    """Normalize a domain string before comparison."""
    if value is None:
        return ""

    candidate = str(value).strip().lower().rstrip(".")
    if not candidate:
        return ""

    if any(token in candidate for token in ("//", "/", "?", "#", ":")):
        try:
            parsed = urlsplit(candidate if "://" in candidate else f"//{candidate}")
        except ValueError:
            parsed = None

        if parsed is not None and parsed.hostname:
            candidate = parsed.hostname

    return candidate.rstrip(".")


def consent_gate(consent, expected_domain):
    """Return True only when the provided consent matches the expected domain."""
    if consent is None or expected_domain is None:
        return False

    consent_value = _normalize_domain(consent)
    expected_value = _normalize_domain(expected_domain)

    if not consent_value or not expected_value:
        return False

    return consent_value == expected_value


def is_consent_allowed(consent, expected_domain):
    """Compatibility wrapper for consent logic."""
    return consent_gate(consent, expected_domain)


class ConsentGate:
    """Simple domain-consent validator."""

    def verify(self, consent, expected_domain):
        return consent_gate(consent, expected_domain)

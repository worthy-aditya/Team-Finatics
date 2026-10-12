from unittest.mock import Mock

from access_guard import AccessGuard, access_guard, is_access_valid


def test_access_guard_requires_session_consent_domain_allowlist_and_access_match():
    response = Mock()
    response.url = "https://example.com/"
    response.status_code = 200

    session = Mock()
    session.get.return_value = response

    assert access_guard(session, "example.com", "example.com", "example.com", ["example.com"], "access") is True
    assert access_guard(session, "example.com", "example.com", "example.com", ["example.com"], "other") is False
    assert access_guard(session, "example.com", "example.com", "example.org", ["example.com"], "access") is False


def test_access_guard_rejects_missing_or_failed_values():
    class FailedRequestSession:
        def get(self, *_args, **_kwargs):
            raise RuntimeError("unreachable")

    assert access_guard(FailedRequestSession(), "example.com", "example.com", "example.com", ["example.com"], "access") is False
    assert is_access_valid(None, "example.com", "example.com", "example.com", ["example.com"], "access") is False
    assert is_access_valid(Mock(), "example.com", None, "example.com", ["example.com"], "access") is False


def test_access_guard_object_uses_same_logic():
    response = Mock()
    response.url = "https://example.com/"
    response.status_code = 200

    session = Mock()
    session.get.return_value = response

    gate = AccessGuard()
    assert gate.verify(session, "example.com", "example.com", "example.com", ["example.com"], "access") is True
    assert gate.verify(session, "example.com", "example.com", "example.com", ["example.org"], "access") is False

from unittest.mock import Mock

from session_guard import SessionGuard, is_session_valid, session_guard


def test_session_guard_requires_session_consent_domain_and_allowlist_match():
    response = Mock()
    response.url = "https://example.com/"

    session = Mock()
    session.get.return_value = response

    assert session_guard(session, "example.com", "example.com", "example.com", ["example.com"]) is True
    assert session_guard(session, "example.com", "example.com", "example.com", ["example.org"]) is False
    assert session_guard(session, "example.com", "example.com", "example.org", ["example.com"]) is False


def test_session_guard_rejects_missing_or_failed_values():
    class FailedRequestSession:
        def get(self, *_args, **_kwargs):
            raise RuntimeError("unreachable")

    assert session_guard(FailedRequestSession(), "example.com", "example.com", "example.com", ["example.com"]) is False
    assert is_session_valid(None, "example.com", "example.com", "example.com", ["example.com"]) is False
    assert is_session_valid(Mock(), "example.com", None, "example.com", ["example.com"]) is False


def test_session_guard_object_uses_same_logic():
    response = Mock()
    response.url = "https://example.com/"

    session = Mock()
    session.get.return_value = response

    gate = SessionGuard()
    assert gate.verify(session, "example.com", "example.com", "example.com", ["example.com"]) is True
    assert gate.verify(session, "example.com", "example.com", "example.com", ["example.org"]) is False

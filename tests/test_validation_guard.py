from unittest.mock import Mock

from validation_guard import ValidationGuard, is_validation_valid, validation_guard


def test_validation_guard_requires_valid_session_consent_domain_and_validation_match():
    response = Mock()
    response.url = "https://example.com/"
    response.status_code = 200

    session = Mock()
    session.get.return_value = response

    assert validation_guard(session, "example.com", "example.com", "example.com", ["example.com"], "validation") is True
    assert validation_guard(session, "example.com", "example.com", "example.com", ["example.com"], "other") is False
    assert validation_guard(session, "example.com", "example.com", "example.org", ["example.com"], "validation") is False


def test_validation_guard_rejects_missing_or_failed_values():
    class FailedRequestSession:
        def get(self, *_args, **_kwargs):
            raise RuntimeError("unreachable")

    assert validation_guard(FailedRequestSession(), "example.com", "example.com", "example.com", ["example.com"], "validation") is False
    assert is_validation_valid(None, "example.com", "example.com", "example.com", ["example.com"], "validation") is False
    assert is_validation_valid(Mock(), "example.com", None, "example.com", ["example.com"], "validation") is False


def test_validation_guard_object_uses_same_logic():
    response = Mock()
    response.url = "https://example.com/"
    response.status_code = 200

    session = Mock()
    session.get.return_value = response

    gate = ValidationGuard()
    assert gate.verify(session, "example.com", "example.com", "example.com", ["example.com"], "validation") is True
    assert gate.verify(session, "example.com", "example.com", "example.com", ["example.org"], "validation") is False

from unittest.mock import Mock

from policy_guard import PolicyGuard, is_policy_guard_valid, policy_guard


def test_policy_guard_requires_valid_session_consent_domain_and_policy_match():
    response = Mock()
    response.url = "https://example.com/"
    response.status_code = 200

    session = Mock()
    session.get.return_value = response

    assert policy_guard(session, "example.com", "example.com", "example.com", ["example.com"], "policy") is True
    assert policy_guard(session, "example.com", "example.com", "example.com", ["example.com"], "other") is False
    assert policy_guard(session, "example.com", "example.com", "example.org", ["example.com"], "policy") is False


def test_policy_guard_rejects_missing_or_failed_values():
    class FailedRequestSession:
        def get(self, *_args, **_kwargs):
            raise RuntimeError("unreachable")

    assert policy_guard(FailedRequestSession(), "example.com", "example.com", "example.com", ["example.com"], "policy") is False
    assert is_policy_guard_valid(None, "example.com", "example.com", "example.com", ["example.com"], "policy") is False
    assert is_policy_guard_valid(Mock(), "example.com", None, "example.com", ["example.com"], "policy") is False


def test_policy_guard_object_uses_same_logic():
    response = Mock()
    response.url = "https://example.com/"
    response.status_code = 200

    session = Mock()
    session.get.return_value = response

    gate = PolicyGuard()
    assert gate.verify(session, "example.com", "example.com", "example.com", ["example.com"], "policy") is True
    assert gate.verify(session, "example.com", "example.com", "example.com", ["example.org"], "policy") is False

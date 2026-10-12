from unittest.mock import Mock

from audit_guard import AuditGuard, audit_guard, is_audit_valid


def test_audit_guard_requires_session_consent_domain_allowlist_and_audit_match():
    response = Mock()
    response.url = "https://example.com/"
    response.status_code = 200

    session = Mock()
    session.get.return_value = response

    assert audit_guard(session, "example.com", "example.com", "example.com", ["example.com"], "audit") is True
    assert audit_guard(session, "example.com", "example.com", "example.com", ["example.com"], "other") is False
    assert audit_guard(session, "example.com", "example.com", "example.org", ["example.com"], "audit") is False


def test_audit_guard_rejects_missing_or_failed_values():
    class FailedRequestSession:
        def get(self, *_args, **_kwargs):
            raise RuntimeError("unreachable")

    assert audit_guard(FailedRequestSession(), "example.com", "example.com", "example.com", ["example.com"], "audit") is False
    assert is_audit_valid(None, "example.com", "example.com", "example.com", ["example.com"], "audit") is False
    assert is_audit_valid(Mock(), "example.com", None, "example.com", ["example.com"], "audit") is False


def test_audit_guard_object_uses_same_logic():
    response = Mock()
    response.url = "https://example.com/"
    response.status_code = 200

    session = Mock()
    session.get.return_value = response

    gate = AuditGuard()
    assert gate.verify(session, "example.com", "example.com", "example.com", ["example.com"], "audit") is True
    assert gate.verify(session, "example.com", "example.com", "example.com", ["example.org"], "audit") is False

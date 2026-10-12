from unittest.mock import Mock

from compliance_guard import ComplianceGuard, compliance_guard, is_compliance_valid


def test_compliance_guard_requires_valid_session_consent_domain_and_compliance_match():
    response = Mock()
    response.url = "https://example.com/"
    response.status_code = 200

    session = Mock()
    session.get.return_value = response

    assert compliance_guard(session, "example.com", "example.com", "example.com", ["example.com"], "compliance") is True
    assert compliance_guard(session, "example.com", "example.com", "example.com", ["example.com"], "other") is False
    assert compliance_guard(session, "example.com", "example.com", "example.org", ["example.com"], "compliance") is False


def test_compliance_guard_rejects_missing_or_failed_values():
    class FailedRequestSession:
        def get(self, *_args, **_kwargs):
            raise RuntimeError("unreachable")

    assert compliance_guard(FailedRequestSession(), "example.com", "example.com", "example.com", ["example.com"], "compliance") is False
    assert is_compliance_valid(None, "example.com", "example.com", "example.com", ["example.com"], "compliance") is False
    assert is_compliance_valid(Mock(), "example.com", None, "example.com", ["example.com"], "compliance") is False


def test_compliance_guard_object_uses_same_logic():
    response = Mock()
    response.url = "https://example.com/"
    response.status_code = 200

    session = Mock()
    session.get.return_value = response

    gate = ComplianceGuard()
    assert gate.verify(session, "example.com", "example.com", "example.com", ["example.com"], "compliance") is True
    assert gate.verify(session, "example.com", "example.com", "example.com", ["example.org"], "compliance") is False

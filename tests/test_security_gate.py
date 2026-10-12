from unittest.mock import Mock

from security_gate import SecurityGate, is_access_allowed, security_gate


def test_security_gate_requires_both_consent_and_domain_verification():
    response = Mock()
    response.url = "https://example.com/"

    session = Mock()
    session.get.return_value = response

    assert security_gate("example.com", "example.com", "example.com", session=session) is True
    assert security_gate("example.com", "example.com", "example.org", session=session) is False
    assert security_gate("example.org", "example.com", "example.com", session=session) is False


def test_security_gate_rejects_failed_verification_or_missing_values():
    class FailedRequestSession:
        def get(self, *_args, **_kwargs):
            raise RuntimeError("unreachable")

    assert security_gate("example.com", "example.com", "example.com", session=FailedRequestSession()) is False
    assert is_access_allowed(None, "example.com", "example.com") is False
    assert is_access_allowed("example.com", None, "example.com") is False


def test_security_gate_object_uses_same_logic():
    response = Mock()
    response.url = "https://example.com/"

    session = Mock()
    session.get.return_value = response

    gate = SecurityGate()
    assert gate.verify("example.com", "example.com", "example.com", session=session) is True
    assert gate.verify("example.com", "example.com", "example.org", session=session) is False

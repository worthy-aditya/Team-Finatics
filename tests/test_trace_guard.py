from unittest.mock import Mock

from trace_guard import TraceGuard, is_trace_valid, trace_guard


def test_trace_guard_requires_session_consent_domain_allowlist_and_trace_match():
    response = Mock()
    response.url = "https://example.com/"
    response.status_code = 200

    session = Mock()
    session.get.return_value = response

    assert trace_guard(session, "example.com", "example.com", "example.com", ["example.com"], "trace") is True
    assert trace_guard(session, "example.com", "example.com", "example.com", ["example.com"], "other") is False
    assert trace_guard(session, "example.com", "example.com", "example.org", ["example.com"], "trace") is False


def test_trace_guard_rejects_missing_or_failed_values():
    class FailedRequestSession:
        def get(self, *_args, **_kwargs):
            raise RuntimeError("unreachable")

    assert trace_guard(FailedRequestSession(), "example.com", "example.com", "example.com", ["example.com"], "trace") is False
    assert is_trace_valid(None, "example.com", "example.com", "example.com", ["example.com"], "trace") is False
    assert is_trace_valid(Mock(), "example.com", None, "example.com", ["example.com"], "trace") is False


def test_trace_guard_object_uses_same_logic():
    response = Mock()
    response.url = "https://example.com/"
    response.status_code = 200

    session = Mock()
    session.get.return_value = response

    gate = TraceGuard()
    assert gate.verify(session, "example.com", "example.com", "example.com", ["example.com"], "trace") is True
    assert gate.verify(session, "example.com", "example.com", "example.com", ["example.org"], "trace") is False

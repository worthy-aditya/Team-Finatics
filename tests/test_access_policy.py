from unittest.mock import Mock

from access_policy import AccessPolicy, access_policy, is_policy_valid


def test_access_policy_requires_consent_domain_and_allowlist_match():
    response = Mock()
    response.url = "https://example.com/"

    session = Mock()
    session.get.return_value = response

    assert access_policy("example.com", "example.com", "example.com", ["example.com"], session=session) is True
    assert access_policy("example.com", "example.com", "example.com", ["example.org"], session=session) is False
    assert access_policy("example.com", "example.com", "example.org", ["example.com"], session=session) is False


def test_access_policy_rejects_missing_or_failed_values():
    class FailedRequestSession:
        def get(self, *_args, **_kwargs):
            raise RuntimeError("unreachable")

    assert access_policy("example.com", "example.com", "example.com", ["example.com"], session=FailedRequestSession()) is False
    assert is_policy_valid(None, "example.com", "example.com", ["example.com"]) is False
    assert is_policy_valid("example.com", None, "example.com", ["example.com"]) is False


def test_access_policy_object_uses_same_logic():
    response = Mock()
    response.url = "https://example.com/"

    session = Mock()
    session.get.return_value = response

    gate = AccessPolicy()
    assert gate.verify("example.com", "example.com", "example.com", ["example.com"], session=session) is True
    assert gate.verify("example.com", "example.com", "example.com", ["example.org"], session=session) is False

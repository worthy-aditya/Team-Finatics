from unittest.mock import Mock

import pytest

from domain_verifier import DomainVerifier, is_domain_verified, verify_domain


@pytest.mark.parametrize(
    "domain, expected_domain, response_url, expected",
    [
        ("example.com", "example.com", "https://example.com/", True),
        ("https://example.com", "example.com", "https://example.com/", True),
        ("example.com:443", "example.com", "https://example.com/", True),
        ("example.com", "example.org", "https://example.org/", False),
    ],
)
def test_verify_domain_matches_expected_hostname(domain, expected_domain, response_url, expected):
    response = Mock()
    response.url = response_url

    verifier = Mock()
    verifier.get.return_value = response

    assert verify_domain(domain, expected_domain, session=verifier) is expected
    assert is_domain_verified(domain, expected_domain, session=verifier) is expected


def test_verify_domain_returns_false_when_http_request_fails():
    class FailedRequestSession:
        def get(self, *_args, **_kwargs):
            raise RuntimeError("unreachable")

    assert verify_domain("example.com", "example.com", session=FailedRequestSession()) is False
    assert is_domain_verified("example.com", "example.com", session=FailedRequestSession()) is False


def test_domain_verifier_object_uses_same_logic():
    response = Mock()
    response.url = "https://example.com/"

    verifier = Mock()
    verifier.get.return_value = response

    gate = DomainVerifier()
    assert gate.verify("example.com", "example.com", session=verifier) is True
    assert gate.verify("example.com", "example.org", session=verifier) is False

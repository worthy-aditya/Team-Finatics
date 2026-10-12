import pytest

from consent_gate import ConsentGate, consent_gate, is_consent_allowed


@pytest.mark.parametrize(
    "consent, expected_domain, expected",
    [
        ("example.com", "example.com", True),
        ("Example.com", "example.com", True),
        ("example.com ", "example.com", True),
        ("example.org", "example.com", False),
        ("", "example.com", False),
        (None, "example.com", False),
    ],
)
def test_consent_gate_matches_expected_behavior(consent, expected_domain, expected):
    assert consent_gate(consent, expected_domain) is expected
    assert is_consent_allowed(consent, expected_domain) is expected


def test_consent_gate_object_uses_same_logic():
    gate = ConsentGate()

    assert gate.verify("example.com", "example.com") is True
    assert gate.verify("example.org", "example.com") is False
    assert gate.verify("", "example.com") is False

"""
test_owasp_mapper.py

Pytest test cases for owasp_mapper.map_keyword_to_owasp()
"""

from owasp_mapper import map_keyword_to_owasp


def test_sql_injection_maps_to_injection():
    result = map_keyword_to_owasp("sql injection")
    assert result is not None
    assert result["rank"] == "A05:2025"
    assert result["name"] == "Injection"


def test_misconfiguration_maps_correctly():
    result = map_keyword_to_owasp("misconfiguration")
    assert result is not None
    assert result["rank"] == "A02:2025"
    assert result["name"] == "Security Misconfiguration"


def test_access_control_maps_correctly():
    result = map_keyword_to_owasp("broken access control")
    assert result is not None
    assert result["rank"] == "A01:2025"
    assert result["name"] == "Broken Access Control"


def test_authentication_maps_correctly():
    result = map_keyword_to_owasp("weak password policy")
    assert result is not None
    assert result["rank"] == "A07:2025"


def test_logging_maps_correctly():
    result = map_keyword_to_owasp("insufficient logging")
    assert result is not None
    assert result["rank"] == "A09:2025"


def test_unknown_keyword_returns_none():
    result = map_keyword_to_owasp("banana smoothie")
    assert result is None


def test_empty_string_returns_none():
    result = map_keyword_to_owasp("")
    assert result is None


def test_none_input_returns_none():
    result = map_keyword_to_owasp(None)
    assert result is None


def test_case_insensitivity():
    result_lower = map_keyword_to_owasp("sql injection")
    result_upper = map_keyword_to_owasp("SQL INJECTION")
    assert result_lower == result_upper
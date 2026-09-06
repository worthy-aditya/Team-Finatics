"""
test_mitre_mapper.py

Pytest test cases for mitre_mapper.map_keyword_to_technique()
"""

from mitre_mapper import map_keyword_to_technique


def test_phishing_maps_to_technique():
    result = map_keyword_to_technique("phishing")
    assert result is not None
    assert result["id"] == "T1566"
    assert "phishing" in result["name"].lower()


def test_powershell_maps_to_technique():
    result = map_keyword_to_technique("powershell")
    assert result is not None
    assert result["id"].startswith("T1059")
    assert "powershell" in result["name"].lower()


def test_result_has_expected_fields():
    result = map_keyword_to_technique("phishing")
    assert result is not None
    assert "id" in result
    assert "name" in result
    assert "description" in result


def test_technique_id_format():
    result = map_keyword_to_technique("phishing")
    assert result is not None
    # T-number format: starts with "T", followed by digits (optionally .subtechnique)
    assert result["id"][0] == "T"
    assert result["id"][1:].replace(".", "").isdigit()


def test_case_insensitivity():
    result_lower = map_keyword_to_technique("phishing")
    result_upper = map_keyword_to_technique("PHISHING")
    assert result_lower == result_upper


def test_unknown_keyword_returns_none():
    result = map_keyword_to_technique("this is not a real technique xyz123")
    assert result is None


def test_empty_string_returns_none():
    result = map_keyword_to_technique("")
    assert result is None


def test_none_input_returns_none():
    result = map_keyword_to_technique(None)
    assert result is None
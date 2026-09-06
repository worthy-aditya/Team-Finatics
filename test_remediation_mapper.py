"""
test_remediation_mapper.py

Pytest test cases for remediation_mapper.py
"""

from remediation_mapper import (
    get_remediation,
    get_remediation_for_findings,
    REMEDIATION_MAP,
)


def test_owasp_remediation_returned_for_known_rank():
    finding = {
        "keyword": "sql injection",
        "owasp": {"rank": "A05:2025", "name": "Injection"},
        "mitre": None,
    }
    result = get_remediation(finding)
    assert result["owasp_remediation"] is not None
    assert len(result["owasp_remediation"]) > 0
    assert any("parameterized" in step.lower() for step in result["owasp_remediation"])


def test_mitre_remediation_returned_for_known_technique():
    finding = {
        "keyword": "phishing",
        "owasp": None,
        "mitre": {"id": "T1566", "name": "Phishing", "domain": "enterprise"},
    }
    result = get_remediation(finding)
    assert result["mitre_remediation"] is not None
    assert len(result["mitre_remediation"]) > 0
    assert any("mfa" in step.lower() or "authentication" in step.lower()
               for step in result["mitre_remediation"])


def test_mitre_remediation_handles_subtechnique_fallback():
    """
    T1059.002 isn't explicitly mapped (only the parent T1059 and the
    specific sub-technique T1059.001 are), so this should fall back to
    the parent T1059 entry rather than the generic fallback.
    """
    finding = {
        "keyword": "applescript",
        "owasp": None,
        "mitre": {"id": "T1059.002", "name": "AppleScript", "domain": "enterprise"},
    }
    result = get_remediation(finding)
    assert result["mitre_remediation"] is not None
    # Should match the parent T1059 list, not the generic fallback
    assert result["mitre_remediation"] == get_remediation(
        {"keyword": "x", "owasp": None,
         "mitre": {"id": "T1059", "name": "Command and Scripting Interpreter", "domain": "enterprise"}}
    )["mitre_remediation"]


def test_mitre_remediation_uses_generic_fallback_for_unmapped_technique():
    finding = {
        "keyword": "obscure technique",
        "owasp": None,
        "mitre": {"id": "T9999", "name": "Nonexistent Technique", "domain": "enterprise"},
    }
    result = get_remediation(finding)
    assert result["mitre_remediation"] is not None
    assert any("mitigation" in step.lower() for step in result["mitre_remediation"])


def test_remediation_none_for_no_owasp_or_mitre_match():
    finding = {"keyword": "unknown thing", "owasp": None, "mitre": None}
    result = get_remediation(finding)
    assert result["owasp_remediation"] is None
    assert result["mitre_remediation"] is None


def test_remediation_handles_empty_dict_gracefully():
    result = get_remediation({})
    assert result["owasp_remediation"] is None
    assert result["mitre_remediation"] is None


def test_remediation_handles_none_input_gracefully():
    result = get_remediation(None)
    assert result["keyword"] is None
    assert result["owasp_remediation"] is None
    assert result["mitre_remediation"] is None


def test_get_remediation_for_findings_batch():
    findings = [
        {"keyword": "sql injection", "owasp": {"rank": "A05:2025", "name": "Injection"}, "mitre": None},
        {"keyword": "phishing", "owasp": None,
         "mitre": {"id": "T1566", "name": "Phishing", "domain": "enterprise"}},
    ]
    results = get_remediation_for_findings(findings)
    assert len(results) == 2
    for result in results:
        assert "keyword" in result
        assert "owasp_remediation" in result
        assert "mitre_remediation" in result


def test_get_remediation_for_findings_empty_list():
    assert get_remediation_for_findings([]) == []


def test_all_owasp_categories_have_remediation_steps():
    expected_ranks = [f"A0{i}:2025" for i in range(1, 10)] + ["A10:2025"]
    for rank in expected_ranks:
        assert rank in REMEDIATION_MAP, f"Missing remediation entry for {rank}"
        assert len(REMEDIATION_MAP[rank]) >= 3, f"{rank} has fewer than 3 remediation steps"
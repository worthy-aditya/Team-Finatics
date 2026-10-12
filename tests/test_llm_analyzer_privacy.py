from unittest.mock import patch

from llm_analyzer import analyze_findings


FINDINGS = [
    {
        "keyword": "sql injection",
        "owasp": {"rank": "A05:2025", "name": "Injection"},
        "mitre": {"id": "T1190", "name": "Exploit Public-Facing Application", "domain": "enterprise"},
    }
]


def test_privacy_mode_blocks_external_llm_calls_via_flag():
    with patch("requests.post") as mock_post:
        result = analyze_findings(FINDINGS, audience="enterprise", use_llm=True, privacy_mode=True)

    assert "Analysis Summary" in result
    assert "1 finding(s) reviewed" in result
    mock_post.assert_not_called()


def test_privacy_mode_blocks_external_llm_calls_via_environment():
    with patch.dict("os.environ", {"PRIVACY_MODE": "true"}, clear=False):
        with patch("requests.post") as mock_post:
            result = analyze_findings(FINDINGS, audience="blue_team", use_llm=True)

    assert "Analysis Summary" in result
    assert "1 finding(s) reviewed" in result
    mock_post.assert_not_called()

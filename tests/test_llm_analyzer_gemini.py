from unittest.mock import Mock, patch

from llm_analyzer import _build_gemini_prompt, analyze_findings


def test_analyze_findings_prefers_gemini_when_key_is_available():
    findings = [
        {
            "keyword": "phishing",
            "owasp": None,
            "mitre": {"id": "T1566", "name": "Phishing", "domain": "enterprise"},
        }
    ]

    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "Gemini summary"}]}}]
    }

    with patch.dict("os.environ", {"GEMINI_API_KEY": "secret-key"}, clear=False):
        with patch("requests.post", return_value=response) as mock_post:
            result = analyze_findings(findings, audience="enterprise", use_llm=True)

    assert result == "Gemini summary"
    mock_post.assert_called_once()


def test_analyze_findings_falls_back_when_gemini_key_is_missing():
    findings = [
        {
            "keyword": "phishing",
            "owasp": None,
            "mitre": {"id": "T1566", "name": "Phishing", "domain": "enterprise"},
        }
    ]

    with patch.dict("os.environ", {}, clear=True):
        result = analyze_findings(findings, audience="enterprise", use_llm=True)

    assert "Analysis Summary" in result
    assert "1 finding(s) reviewed" in result


def test_build_gemini_prompt_includes_audience_guidance():
    findings = [
        {
            "keyword": "sql injection",
            "owasp": {"rank": "A05:2025", "name": "Injection"},
            "mitre": None,
        }
    ]

    prompt = _build_gemini_prompt(findings, audience="blue_team")

    assert "blue_team" not in prompt.lower()
    assert "defensive" in prompt.lower()
    assert "sql injection" in prompt
    assert "OWASP Top 10:2025" in prompt

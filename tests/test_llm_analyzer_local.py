from unittest.mock import Mock, patch

from llm_analyzer import analyze_findings


FINDINGS = [
    {
        "keyword": "sql injection",
        "owasp": {"rank": "A05:2025", "name": "Injection"},
        "mitre": {"id": "T1190", "name": "Exploit Public-Facing Application", "domain": "enterprise"},
    }
]


def test_analyze_findings_uses_ollama_when_configured():
    response = Mock()
    response.status_code = 200
    response.json.return_value = {"response": "Ollama summary"}

    with patch.dict(
        "os.environ",
        {"LLM_PROVIDER": "ollama", "OLLAMA_MODEL": "mistral", "OLLAMA_BASE_URL": "http://localhost:11434"},
        clear=False,
    ):
        with patch("requests.post", return_value=response) as mock_post:
            result = analyze_findings(FINDINGS, audience="enterprise", use_llm=True)

    assert result == "Ollama summary"
    mock_post.assert_called_once()
    assert "http://localhost:11434/api/generate" in mock_post.call_args[0][0]


def test_analyze_findings_uses_mistral_local_endpoint_when_configured():
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "choices": [{"message": {"content": "Mistral summary"}}]
    }

    with patch.dict(
        "os.environ",
        {
            "LLM_PROVIDER": "mistral",
            "MISTRAL_MODEL": "mistral-small",
            "MISTRAL_BASE_URL": "http://localhost:11434/v1",
            "MISTRAL_API_KEY": "local-key",
        },
        clear=False,
    ):
        with patch("requests.post", return_value=response) as mock_post:
            result = analyze_findings(FINDINGS, audience="blue_team", use_llm=True)

    assert result == "Mistral summary"
    mock_post.assert_called_once()
    assert "/chat/completions" in mock_post.call_args[0][0]


def test_analyze_findings_falls_back_when_local_provider_is_unavailable():
    with patch.dict(
        "os.environ",
        {"LLM_PROVIDER": "ollama", "OLLAMA_MODEL": "mistral"},
        clear=False,
    ):
        with patch("requests.post", side_effect=ConnectionError("offline")):
            result = analyze_findings(FINDINGS, audience="general", use_llm=True)

    assert "Analysis Summary" in result
    assert "1 finding(s) reviewed" in result

from sentinelai.prompt_engine import LLMProvider, analyze_scan_data


def test_secondary_provider_fallback_on_primary_failure(monkeypatch):
    calls = []

    def fake_gemini(*args, **kwargs):
        calls.append("gemini")
        raise RuntimeError("quota exceeded")

    def fake_ollama(*args, **kwargs):
        calls.append("ollama")
        return "llama3", "fallback analysis", {"prompt_tokens": 10, "response_tokens": 20}

    monkeypatch.setattr("sentinelai.prompt_engine._call_gemini", fake_gemini)
    monkeypatch.setattr("sentinelai.prompt_engine._call_ollama", fake_ollama)

    result = analyze_scan_data({"host": "127.0.0.1", "ports": []}, provider=LLMProvider.GEMINI)

    assert result.provider == LLMProvider.OLLAMA
    assert result.model == "llama3"
    assert result.analysis == "fallback analysis"
    assert calls == ["gemini", "ollama"]


def test_fallback_is_not_triggered_for_same_provider(monkeypatch):
    def fake_gemini(*args, **kwargs):
        raise RuntimeError("forced fail")

    def fake_ollama(*args, **kwargs):
        raise RuntimeError("ollama also failed")

    monkeypatch.setattr("sentinelai.prompt_engine._call_gemini", fake_gemini)
    monkeypatch.setattr("sentinelai.prompt_engine._call_ollama", fake_ollama)

    try:
        analyze_scan_data({"host": "127.0.0.1", "ports": []}, provider=LLMProvider.GEMINI)
        assert False, "Expected RuntimeError for a non-transient provider failure"
    except RuntimeError as exc:
        assert "forced fail" in str(exc)

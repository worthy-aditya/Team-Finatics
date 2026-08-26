"""Day 11 unit tests for the prompt engineering module.

These tests cover the PURE, provider-agnostic prompt-building functions added
in Day 11 (no API key or network required), so they run fast and offline:

- build_prompt() dispatches to the correct template per PromptMode
- build_nmap_analysis_prompt() is a backward-compatible alias
- Each mode's prompt contains its required section headers
- analyze_scan_data() raises NotImplementedError for not-yet-built providers
  (Ollama/Day 12, OpenAI/Claude/Day 13) and requires a Gemini API key

Run with:  python -m pytest tests/test_prompt_engine.py -v
(pytest is planned for the Week 3 test suite; Sneha will install it.
These tests can also be executed as a plain script for offline validation.)
"""

import json
import os
import sys
from pathlib import Path

import requests

# Make the repo importable when running as a plain script.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# pytest is planned for the Week 3 test suite (Sneha). The pure-function tests
# below degrade gracefully and run via __main__ even without pytest installed.
try:
    import pytest
except ImportError:  # pragma: no cover - offline fallback
    pytest = None

    class _MarkNamespace:
        """Namespace providing @pytest.mark.parametrize as a no-op decorator."""

        @staticmethod
        def parametrize(argnames, argvalues):
            def deco(f):
                return f
            return deco

    class _PytestStub:
        """Minimal stand-in for offline runs without pytest installed."""

        mark = _MarkNamespace()

        @staticmethod
        def raises(expected_exception, *args, **kwargs):
            class _CM:
                def __init__(self_inner):
                    self_inner.exc = None
                def __enter__(self_inner):
                    return self_inner
                def __exit__(self_inner, exc_type, exc, tb):
                    if exc is None:
                        raise AssertionError(
                            f"DID NOT RAISE {expected_exception.__name__}"
                        )
                    if not issubclass(exc_type, expected_exception):
                        return False
                    self_inner.exc = exc
                    return True
                def __getattr__(self_inner, name):
                    return getattr(self_inner.exc, name)
            return _CM()

    pytest = _PytestStub()

from sentinelai.prompt_engine import (  # noqa: E402
    DEFAULT_GEMINI_MODELS,
    LLMProvider,
    PromptMode,
    ScanAnalysisResult,
    analyze_scan_data,
    build_nmap_analysis_prompt,
    build_prompt,
    default_models_for_provider,
    load_scan_data,
)

SAMPLE_SCAN = {
    "nmap": {"version": "7.94", "scan_type": "syn"},
    "hosts": [{"addresses": {"ipv4": "127.0.0.1"}, "status": "up"}],
    "scan": {
        "tcp": {
            "135": {"state": "open", "product": "msrpc", "version": ""},
            "445": {"state": "open", "product": "microsoft-ds", "version": ""},
        }
    }
}
# ---------------------------------------------------------------------------
# build_prompt / build_nmap_analysis_prompt
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "mode,expected_headers",
    [
        (
            PromptMode.STANDARD,
            [
                "## 1. Plain-English Summary",
                "## 2. Risk Findings (ranked)",
                "## 3. Attacker Perspective",
                "## 4. Recommended Next Steps",
                "## 5. Confidence & Limitations",
            ],
        ),
        (
            PromptMode.BEGINNER,
            [
                "## 1. What is this scan about?",
                "## 2. What did we see?",
                "## 3. Easy risk ratings",
                "## 4. What should we do next?",
                "## 5. Glossary",
            ],
        ),
        (
            PromptMode.REMEDIATION,
            [
                "## 1. Executive Summary",
                "## 2. Prioritized Action List",
                "## 3. Compliance Cross-Check",
                "## 4. Verification Plan",
            ],
        ),
    ],
)
def test_build_prompt_has_expected_sections(mode, expected_headers):
    prompt = build_prompt(SAMPLE_SCAN, mode=mode)
    for header in expected_headers:
        assert header in prompt, f"{mode.value} prompt missing: {header}"


def test_build_prompt_includes_scan_data():
    prompt = build_prompt(SAMPLE_SCAN, mode=PromptMode.STANDARD)
    assert json.dumps(SAMPLE_SCAN, indent=2) in prompt


def test_build_nmap_analysis_prompt_backward_compatible():
    assert build_nmap_analysis_prompt(SAMPLE_SCAN) == build_prompt(
        SAMPLE_SCAN, mode=PromptMode.STANDARD
    )
    assert build_nmap_analysis_prompt(SAMPLE_SCAN, mode=PromptMode.BEGINNER) == (
        build_prompt(SAMPLE_SCAN, mode=PromptMode.BEGINNER)
    )


def test_default_mode_is_standard():
        assert build_prompt(SAMPLE_SCAN).split("## ")[1].startswith("1. Plain-English")


# ---------------------------------------------------------------------------
# Provider helpers
# ---------------------------------------------------------------------------

def test_default_models_for_provider_gemini():
    models = default_models_for_provider(LLMProvider.GEMINI)
    assert "gemini-2.0-flash" in models
    assert DEFAULT_GEMINI_MODELS[-1] in models


def test_ollama_unreachable_gives_clear_error():
    """If the local Ollama server is down, users get an actionable error."""
    import sentinelai.prompt_engine as pe

    class _ConnErr:
        exceptions = requests.exceptions  # real exception classes for except clauses

        def get(self, *a, **k):
            raise requests.exceptions.ConnectionError("refused")

    saved = pe.requests
    try:
        pe.requests = _ConnErr()
        with pytest.raises(RuntimeError, match="Cannot reach Ollama server"):
            analyze_scan_data(SAMPLE_SCAN, provider=LLMProvider.OLLAMA)
    finally:
        pe.requests = saved


def test_ollama_generate_parses_response():
    """_call_ollama posts to /api/generate and parses text + usage correctly."""
    import sentinelai.prompt_engine as pe

    class _FakeResp:
        status_code = 200

        def raise_for_status(self_inner):
            pass

        def json(self_inner):
            return {
                "model": "gemma4",
                "response": "## 1. Plain-English Summary\nLocalhost looks fine.",
                "prompt_eval_count": 120,
                "eval_count": 340,
                "total_duration": 5_000_000_000,
            }

    class _FakeRequests:
        def get(self_inner, url, **k):
            class _Tags:
                status_code = 200

                def raise_for_status(self):
                    pass

                def json(self):
                    return {"models": [{"name": "gemma4:latest"}]}

            return _Tags()

        def post(self_inner, url, json=None, **k):
            assert url.endswith("/api/generate")
            assert json["model"] == "gemma4:latest"
            assert json["stream"] is False
            return _FakeResp()

    saved = pe.requests
    try:
        pe.requests = _FakeRequests()
        result = analyze_scan_data(SAMPLE_SCAN, provider=LLMProvider.OLLAMA)
        assert result.provider is LLMProvider.OLLAMA
        assert result.model == "gemma4:latest"
        assert result.analysis.startswith("## 1. Plain-English Summary")
        assert result.usage["prompt_tokens"] == 120
        assert result.usage["response_tokens"] == 340
    finally:
        pe.requests = saved


def test_ollama_missing_model_advances_to_next_candidate():
    """A 404 (model not pulled) advances to the next candidate instead of failing."""
    import sentinelai.prompt_engine as pe

    requested_models = []

    class _Resp404:
        status_code = 404

        def raise_for_status(self_inner):
            raise requests.exceptions.HTTPError("404")

        def json(self_inner):
            return {}

    class _RespOK:
        status_code = 200

        def raise_for_status(self_inner):
            pass

        def json(self_inner):
            return {
                "model": "gemma4",
                "response": "ok-analysis",
                "prompt_eval_count": 10,
                "eval_count": 20,
                "total_duration": 1_000_000,
            }

    class _FakeRequests:
        def get(self_inner, url, **k):
            class _Tags:
                status_code = 200

                def raise_for_status(self):
                    pass

                def json(self):
                    return {"models": [{"name": "llama3"}, {"name": "gemma4"}]}

            return _Tags()

        def post(self_inner, url, json=None, **k):
            requested_models.append(json["model"])
            return _Resp404() if json["model"] == "llama3" else _RespOK()

    saved = pe.requests
    try:
        pe.requests = _FakeRequests()
        model, text, usage = pe._call_ollama(prompt="p", retries=0)
        # llama3 was missing (404); gemma4 answered.
        assert model == "gemma4"
        assert text == "ok-analysis"
        assert requested_models[0] == "llama3"
    finally:
        pe.requests = saved


def test_openai_provider_not_implemented_yet():
    """OpenAI/Claude (Day 13) must raise explicitly, not silently misbehave."""
    with pytest.raises(NotImplementedError):
        analyze_scan_data(SAMPLE_SCAN, provider=LLMProvider.OPENAI)
    with pytest.raises(NotImplementedError):
        analyze_scan_data(SAMPLE_SCAN, provider=LLMProvider.CLAUDE)


def test_gemini_requires_api_key(monkeypatch=None):
    """Without a key (and without .env loading), analyze_scan_data raises clearly."""
    import sentinelai.prompt_engine as pe

    saved_key = os.environ.pop("GEMINI_API_KEY", None)
    saved_load_dotenv = pe.load_dotenv
    pe.load_dotenv = lambda *a, **k: False  # neutralize .env auto-loading
    try:
        with pytest.raises(RuntimeError, match="GEMINI_API_KEY is not set"):
            analyze_scan_data(SAMPLE_SCAN, provider=LLMProvider.GEMINI)
    finally:
        pe.load_dotenv = saved_load_dotenv
        if saved_key is not None:
            os.environ["GEMINI_API_KEY"] = saved_key


# ---------------------------------------------------------------------------
# ScanAnalysisResult dataclass
# ---------------------------------------------------------------------------

def test_scan_analysis_result_field_defaults():
    result = ScanAnalysisResult(
        provider=LLMProvider.GEMINI, model="test", analysis="hi"
    )
    assert result.prompt == ""
    assert result.raw is None
    assert result.usage == {}


# ---------------------------------------------------------------------------
# Day 13: LLM switcher (resolve_provider)
# ---------------------------------------------------------------------------

import sentinelai.prompt_engine as pe  # noqa: E402


def test_resolve_provider_free_paths():
    """The two FREE providers map cleanly (case-insensitive)."""
    assert pe.resolve_provider("gemini") is LLMProvider.GEMINI
    assert pe.resolve_provider("OLLAMA") is LLMProvider.OLLAMA
    assert pe.resolve_provider(" Ollama ") is LLMProvider.OLLAMA


def test_resolve_provider_paid_pending():
    """openai/claude are accepted by the switcher but fail with guidance."""
    for name in ("openai", "claude"):
        with pytest.raises(RuntimeError, match="not wired up yet.*free providers", ):
            pe.resolve_provider(name)


def test_resolve_provider_unknown():
    with pytest.raises(RuntimeError, match="Unknown LLM provider"):
        pe.resolve_provider("chatgpt")


if __name__ == "__main__":
    # Offline execution without pytest: run the pure-function checks.
    test_build_prompt_has_expected_sections(PromptMode.STANDARD, [
        "## 1. Plain-English Summary",
        "## 2. Risk Findings (ranked)",
        "## 3. Attacker Perspective",
        "## 4. Recommended Next Steps",
        "## 5. Confidence & Limitations",
    ])
    test_build_prompt_has_expected_sections(PromptMode.BEGINNER, [
        "## 1. What is this scan about?",
        "## 2. What did we see?",
        "## 3. Easy risk ratings",
        "## 4. What should we do next?",
        "## 5. Glossary",
    ])
    test_build_prompt_has_expected_sections(PromptMode.REMEDIATION, [
        "## 1. Executive Summary",
        "## 2. Prioritized Action List",
        "## 3. Compliance Cross-Check",
        "## 4. Verification Plan",
    ])
    test_build_prompt_includes_scan_data()
    test_build_nmap_analysis_prompt_backward_compatible()
    test_default_mode_is_standard()
    test_default_models_for_provider_gemini()
    test_ollama_unreachable_gives_clear_error()
    test_ollama_generate_parses_response()
    test_ollama_missing_model_advances_to_next_candidate()
    test_openai_provider_not_implemented_yet()
    test_gemini_requires_api_key(None)  # offline: monkeypatch unused
    test_scan_analysis_result_field_defaults()
    test_resolve_provider_free_paths()
    test_resolve_provider_paid_pending()
    test_resolve_provider_unknown()
    print("ALL prompt_engine TESTS PASSED (offline, pure functions)")

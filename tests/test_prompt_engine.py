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


def test_ollama_provider_not_implemented_yet():
    """Day 11 wires only Gemini; Ollama (Day 12) must raise explicitly."""
    with pytest.raises(NotImplementedError):
        analyze_scan_data(SAMPLE_SCAN, provider=LLMProvider.OLLAMA)


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
    test_ollama_provider_not_implemented_yet()
    test_openai_provider_not_implemented_yet()
    test_gemini_requires_api_key(None)  # offline: monkeypatch unused
    test_scan_analysis_result_field_defaults()
    print("ALL Day 11 prompt_engine TESTS PASSED (offline, pure functions)")

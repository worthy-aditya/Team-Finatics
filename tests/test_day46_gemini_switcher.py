"""Day 46: the --llm gemini switch returns analysis from both CLI entry points."""

from importlib import import_module

import pytest
from click.testing import CliRunner

from sentinelai.prompt_engine import LLMProvider


@pytest.mark.parametrize("entry_point", ["package", "root"])
@pytest.mark.parametrize("kind", ["scan", "events"])
def test_gemini_switcher_returns_analysis(monkeypatch, entry_point, kind):
    package_cli = import_module("sentinelai.cli")
    root_cli = import_module("commands.analyze")
    module = package_cli if entry_point == "package" else root_cli
    command = package_cli.main if entry_point == "package" else root_cli.analyze
    calls = []

    def fake_analyze(**kwargs):
        calls.append(kwargs)
        return "gemini-test-model", "Gemini analysis text returned successfully."

    monkeypatch.setattr(module, "analyze_scan_file", fake_analyze)
    monkeypatch.setattr(module, "analyze_event_log_file", fake_analyze)

    result = CliRunner().invoke(
        command,
        ["analyze", "--input", "fixture.json", "--kind", kind, "--llm", "gemini", "--no-save"]
        if entry_point == "package"
        else ["--input", "fixture.json", "--kind", kind, "--llm", "gemini", "--no-save"],
    )

    assert result.exit_code == 0, result.output
    assert "Gemini analysis text returned successfully." in result.output
    assert len(calls) == 1
    assert calls[0]["provider"] is LLMProvider.GEMINI
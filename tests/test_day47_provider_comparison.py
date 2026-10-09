"""Offline checks for the Day 47 provider comparison harness."""

import hashlib

import pytest

from day47_provider_comparison import build_cases, extract_text, render_report


@pytest.mark.parametrize("provider", ["openai", "anthropic", "gemini", "ollama"])
def test_synthetic_prompts_are_stable_and_use_reserved_addresses(provider):
    first = build_cases()
    second = build_cases()

    assert [case["case"] for case in first] == [
        "Synthetic Nmap scan",
        "Synthetic Windows event log",
    ]
    for left, right in zip(first, second):
        assert left["prompt"] == right["prompt"]
        assert hashlib.sha256(left["prompt"].encode()).hexdigest()
    combined = "\n".join(case["prompt"] for case in first)
    assert "192.0.2.10" in combined
    assert "203.0.113.42" in combined
    assert "DESKTOP-7H3XK2D" not in combined


@pytest.mark.parametrize(
    ("provider", "payload", "expected"),
    [
        ("openai", {"choices": [{"message": {"content": "openai text"}}]}, "openai text"),
        ("anthropic", {"content": [{"type": "text", "text": "anthropic text"}]}, "anthropic text"),
        ("gemini", {"candidates": [{"content": {"parts": [{"text": "gemini text"}]}}]}, "gemini text"),
        ("ollama", {"response": "ollama text"}, "ollama text"),
    ],
)
def test_extract_text_for_each_provider(provider, payload, expected):
    assert extract_text(provider, payload) == expected


def test_report_records_all_providers_and_exact_prompt_hashes():
    cases = build_cases()
    rows = []
    for case in cases:
        for provider in ("GPT-4o", "Claude Sonnet 5.5", "Gemini Flash", "Ollama Gemma 4"):
            rows.append(
                {
                    "case": case["case"],
                    "provider": provider,
                    "status": "OK",
                    "requested_model": "test-model",
                    "reported_model": "test-model",
                    "elapsed_seconds": 0.1,
                    "usage": {"total_tokens": 10},
                    "prompt_sha256": hashlib.sha256(case["prompt"].encode()).hexdigest(),
                    "output": "synthetic test output",
                }
            )
    report = render_report(rows, generated_at="2026-10-07T00:00:00+00:00")
    assert report.count("| OK |") == 8
    assert "synthetic test output" in report
    assert "descriptive comparison, not an accuracy ranking" in report

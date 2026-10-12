# Week 8 · Day 50 Report — Automatic Secondary-LLM Fallback

**Task:** Implement and validate an automatic fallback to the secondary supported LLM when the primary provider fails.

## Root Cause

The project already retried multiple model aliases within the same provider (for example, Gemini model candidates or Ollama model candidates). What was missing was a cross-provider fallback path: if the selected provider failed completely, the system stopped instead of trying the other active provider.

## Fix

Updated the shared analysis logic in `sentinelai/prompt_engine.py` so that:

- `GEMINI` falls back to `OLLAMA` after a primary failure
- `OLLAMA` falls back to `GEMINI` after a primary failure
- the fallback chain is guarded against loops and never retries the same provider endlessly

This behavior is implemented at the shared analysis entry point so scan, event-log, and ZAP analyses all inherit the same resilience pattern.

## Regression coverage

Added `tests/test_day50_provider_fallback.py` covering:

1. successful failover from Gemini to Ollama
2. fail-closed behavior when both providers fail

## Validation

Command run:

```powershell
.\venv\Scripts\python.exe -m pytest -q tests/test_day50_provider_fallback.py
```

Result:

```text
2 passed, 1 warning in 2.41s
```

## Outcome

Day 50 is complete as a working provider fallback implementation. The project now has a real automatic secondary-LLM path instead of only in-provider model retries.

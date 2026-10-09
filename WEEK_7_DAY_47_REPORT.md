# Week 7 - Day 47 Report (Four-Provider Comparison)

**Date:** 2026-10-07  
**Owner:** Aditya Gupta  
**Plan task:** Run identical Nmap and Windows Event Log prompts across GPT-4o, Claude, Gemini, and Ollama; log all provider results.  
**Status:** INCOMPLETE — both local Ollama prompts produced text on follow-up (the event response hit its output cap); cloud comparisons remain blocked by provider errors.

---

## 1. Method

Added [day47_provider_comparison.py](day47_provider_comparison.py) and [tests/test_day47_provider_comparison.py](tests/test_day47_provider_comparison.py). The runner builds one synthetic Nmap prompt and one synthetic Windows event-log prompt, hashes each prompt, and sends identical text to the four configured provider/model selections:

- OpenAI GPT-4o (`gpt-4o`)
- Claude Sonnet 5.5 (`claude-sonnet-5-5`)
- Gemini Flash (`gemini-flash-latest`)
- Local Ollama Gemma 4 (`gemma4:latest`)

The fixtures use reserved documentation IP ranges and sample account/host names only. No real scan data or personal event logs were sent. Each output was capped at 1,000 tokens; the harness performs no application-level retries or model fallback.

## 2. Results

The generated artifact [day47_provider_comparison.md](day47_provider_comparison.md) contains the exact prompts, matching SHA-256 hashes per scenario, selected models, timings, statuses, and provider errors. [day47_ollama_followup.md](day47_ollama_followup.md) records the local follow-up responses.

| Provider | Synthetic Nmap prompt | Synthetic event prompt |
|---|---|---|
| GPT-4o | HTTP 401 Unauthorized | HTTP 401 Unauthorized |
| Claude Sonnet 5.5 | HTTP 401 Unauthorized | HTTP 401 Unauthorized |
| Gemini Flash | HTTP 503 Service Unavailable; provider reported high demand | HTTP 503 Service Unavailable; provider reported high demand |
| Ollama Gemma 4 | Text returned with thinking disabled; 948 output tokens | Text returned with thinking disabled; 1,000-token cap truncated response |

A separate minimal localhost-only Ollama smoke prompt also succeeded. The initial full-prompt Ollama attempt returned HTTP 500/empty visible text; response metadata showed the event prompt used its token budget for thinking (`done_reason: length`). With Ollama's optional thinking disabled, both prompts returned visible analysis; the event response still reached the 1,000-token cap and is incomplete.

## 3. Validation

The offline test suite `tests/test_day47_provider_comparison.py` passed **9 tests** covering deterministic synthetic prompts, reserved test addresses, response parsing for all four providers, and report rendering. Local Ollama outputs are captured in the follow-up artifact; no live outputs were fabricated.

The OpenAI and Anthropic key environment variables were present, but the providers rejected the credentials. Key values were not displayed. Gemini was temporarily unavailable. Ollama's full-prompt 500 remains undiagnosed.

## 4. Safety and Cost

Exactly two synthetic prompts were submitted to each of the three cloud endpoints; no real customer, host, scan, or event-log data was sent. The REST runner issued no explicit retry or fallback. Provider-side billing/usage for failed requests is account-specific and cannot be determined from this workspace; check each provider's usage dashboard.

## 5. Resume Criteria

Day 47 remains incomplete until actual outputs are recorded for all four providers on both identical prompts, with a complete event response. Before another run:

1. Verify/replace the OpenAI and Anthropic API credentials in the local ignored `.env` file; do not paste secrets into chat.
2. Retry Gemini only after service availability returns and after approval for another cloud request batch.
3. Increase the Ollama output cap or use a concise prompt/output requirement so the event response completes, while keeping the exact same prompt text across all providers.
4. Rerun the comparison and preserve successful responses, model IDs, token usage, and errors.

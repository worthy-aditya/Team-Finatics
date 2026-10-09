# Gemini API Research Notes

**Plan:** Week 7, Day 45 (Aditya Gupta)  
**Prepared:** 2026-10-07  
**Purpose:** Wiki-ready research on Gemini API authentication, the Python SDK, and rate limits, grounded in Google's current documentation and SentinelAI's existing integration.  
**Publication:** Published to the [Team Finatics GitHub Wiki](https://github.com/worthy-aditya/Team-Finatics/wiki/Gemini-API-Research) on 2026-10-07.

## Executive Summary

SentinelAI already calls Gemini through Google's supported GenAI Python SDK. The project reads `GEMINI_API_KEY`, creates `google.genai.Client`, and sends text with `client.models.generate_content()`. The main operational points for the upcoming integration work are:

1. API keys are credentials, not public identifiers. Keep them out of source control and use a local environment variable or a secret manager.
2. Google AI Studio's key model changed on May 28, 2026: new keys are authorization keys by default. Unrestricted standard keys are rejected; existing standard keys need explicit restrictions to continue working.
3. Gemini limits are project- and model-dependent. Check the actual project's current limits in AI Studio; do not hard-code published example quotas or assume a free-tier limit is guaranteed.
4. The code already retries selected transient errors and rotates through configured model candidates. Day 46 should review this against the current SDK/model list and test without exposing a key or triggering unnecessary paid usage.

## 1. Authentication and Key Handling

### Current Google key types

Google documents two Gemini API key types:

- **Standard API key:** identifies the Google Cloud project for quota and billing, but does not identify a caller.
- **Authorization (auth) API key:** bound to a Google Cloud service account and provides service-account-scoped identity and permissions for Gemini API access.

As documented on the API-key page retrieved on 2026-10-07, keys created in AI Studio from **May 28, 2026** are auth keys by default. Gemini API requests using unrestricted standard keys are rejected. Existing standard keys with explicit restrictions continue to work; Google recommends restricting keys to the Gemini API. Check the key type and current restrictions in AI Studio before diagnosing an authentication failure.

An auth API key is still a secret credential. Do not commit it, paste it into issue trackers, or place it in a command that will be retained in shell history. If a key may have leaked, rotate it and inspect account usage.

### SentinelAI's current configuration

- `.env.example` documents `GEMINI_API_KEY` and says to keep real `.env` values uncommitted.
- `sentinelai/prompt_engine.py` loads dotenv and explicitly passes `GEMINI_API_KEY` into `genai.Client(api_key=...)`.
- The SDK can also discover `GOOGLE_API_KEY`, and Google's SDK documentation says that variable takes precedence if both are set. SentinelAI currently passes `GEMINI_API_KEY` explicitly, so its provider path uses that value rather than relying on automatic discovery.
- No key was read, printed, or used during this Day 45 research task.

## 2. Python SDK and Request Pattern

Google recommends the **Google GenAI SDK** for Python. The package is `google-genai`; the import is `from google import genai`. Google marks the SDK generally available and recommends it over the older `google-generativeai` library, which is no longer actively maintained.

SentinelAI already uses the modern SDK and the `models.generate_content` API. A minimal equivalent request is:

```python
import os
from google import genai

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
response = client.models.generate_content(
    model="gemini-3.8-flash",
    contents="Summarize these security observations for analyst review.",
)
print(response.text)
```

This is an illustrative example, not a call made during research. SentinelAI also sets request timeouts, passes safety configuration, records token-usage metadata where available, and applies model fallback logic.

### Version and model maintenance observations

- `requirements.txt` pins `google-genai==2.13.0`.
- The official SDK repository showed release `2.28.0` during this research. Before upgrading, Day 46 should review SDK changes and run the Gemini and provider regression tests; no dependency upgrade was made on Day 45.
- SentinelAI's current Gemini candidates include `gemini-3.6-flash`, `gemini-flash-latest`, `gemini-3.5-flash`, and `gemini-3.7-flash`; its default is the `gemini-flash-latest` alias.
- Google's model guide lists `gemini-3.8-flash` as a stable model as of this research. A `latest` alias can move to a newer release, while a stable versioned model name is more reproducible. Validate availability, pricing, and output quality before changing SentinelAI's default; no model configuration was changed here.

## 3. Rate Limits, Quotas, and Billing

Google describes limits in multiple dimensions, including:

- requests per minute (RPM);
- input tokens per minute (TPM);
- requests per day (RPD).

The limits are applied per **Google Cloud project**, vary by model and usage tier, and may also include spend-based limits. Google's rate-limit page says RPD resets at midnight Pacific time. Preview and experimental models may have more restrictive limits. Published or example values are not a promise of capacity; check the current project-specific values in [AI Studio Rate Limits](https://aistudio.google.com/rate-limit).

A free tier does not mean every model, request volume, or account has the same quota. Moving to a paid tier requires billing setup and can create charges. Do not enable billing or upgrade a project as part of routine testing without the account owner's approval.

### Relevant errors and response

| HTTP status / condition | Likely meaning | Recommended response |
|---|---|---|
| `401` | Missing, invalid, or expired key | Check the selected key, environment variable, and key status; do not keep retrying unchanged credentials. |
| `403` | Key, project, or permission restriction | Check key type/restrictions, API enablement, project access, and service-account binding. |
| `404` | Model or resource not found | Verify the exact model ID and its current availability; select a documented model. |
| `429 RESOURCE_EXHAUSTED` | Per-minute rate limit, daily quota, or spend limit | Check the exact AI Studio quota/error details; back off for transient limits, reduce request/context/output volume, or wait for a daily reset. Do not treat every 429 as a 60-second reset. |
| `500` / `503` | Transient server failure or service availability issue | Retry with bounded backoff and surface a clear error if it persists. |

SentinelAI currently retries statuses `429`, `500`, and `503` plus timeouts, using 5- and 10-second delays by default, and then attempts configured model candidates. It also displays a rate-limit hint and suggests waiting or switching to Ollama. This is a useful baseline. A future resilience change should distinguish a transient RPM limit from an exhausted daily quota, bound total attempts across all model candidates, and avoid retrying authentication/permission/model-not-found failures.

## 4. Day 46 Implementation Notes

For the planned `--llm gemini` work:

1. Retain the official `google-genai` client and the repository's explicit `GEMINI_API_KEY` configuration unless testing shows a compatibility issue.
2. Verify the exact model ID in Google's model catalog before choosing a default; keep `GEMINI_MODEL` override behavior and test each fallback candidate.
3. Test missing key, invalid/restricted key, unavailable model, transient `429`/`503`, and successful text output without logging credential values.
4. Keep retries bounded; distinguish configuration errors from transient quota/service errors.
5. Run the focused Gemini tests and full regression after any dependency or default-model change.
6. Keep API tests minimal and cost-aware. Confirm the project's usage tier and model pricing before any repeated live test; prefer mocks for error-path tests.

No API integration or Gemini API call was performed; no credential, dependency, or billing changes were made. The research page was subsequently published to the Team Finatics Wiki.

## Sources

All sources below are Google's official Gemini documentation or SDK repository. Retrieved 2026-10-07.

- [Gemini API keys: key types, restrictions, environment variables, and security](https://ai.google.dev/gemini-api/docs/api-key)
- [Gemini API quickstart](https://ai.google.dev/gemini-api/docs/quickstart?lang=python)
- [Gemini API libraries and SDK status](https://ai.google.dev/gemini-api/docs/libraries)
- [Google GenAI Python SDK repository](https://github.com/googleapis/python-genai)
- [Gemini API rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)
- [Gemini API errors](https://ai.google.dev/gemini-api/docs/api-errors)
- [Gemini model catalog](https://ai.google.dev/gemini-api/docs/models)

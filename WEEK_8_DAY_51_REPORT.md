# Week 8 · Day 51 Report — Provider Health Scoring and Recommendations

**Task:** Add a lightweight provider-health model that ranks each active LLM by availability, latency, cost, and privacy fit so the project can recommend the most suitable provider for a task.

## Why this was needed

Day 50 fixed the crash path when a primary provider failed. The next gap was decision support: the project still had no simple way to rate provider suitability for a sensitive or public workload before analysis started.

This was especially important for the project’s two active providers:

- Gemini: strong cloud-first performance and API-backed speed
- Ollama: stronger privacy and local execution fit, but often slower or more variable depending on local hardware

## Feature added

Created the new provider-health helper in `provider_health.py` with:

- `ProviderHealth` dataclass to model each provider’s health snapshot
- `score_provider_health()` to calculate a 0–100 ranking from availability, latency, cost, and privacy preference
- `recommend_provider_for_task()` to rank providers for a task and adjust the result based on:
  - sensitive/private workloads
  - public or low-risk tasks
  - whether a cloud API key is configured

## Logic summary

The ranking favors:

- local/Ollama for private or confidential analysis
- Gemini for public analysis when a valid API key is available and the task is not privacy-sensitive
- a balanced score for mixed or neutral workloads

This keeps the behavior simple, deterministic, and easy to extend later with real telemetry such as latency sampling or uptime tracking.

## Regression coverage

Added `tests/test_day51_provider_health.py` to validate:

1. basic health scoring produces a valid numeric result
2. private/sensitive tasks prefer Ollama
3. public tasks prefer Gemini when the API key is available

## Validation

Command run:

```powershell
.\venv\Scripts\python.exe -m pytest -q tests/test_day51_provider_health.py
```

Result:

```text
3 passed in 0.04s
```

## Outcome

Day 51 is complete: the project now has a provider-ranking layer that supports better task-to-model matching and gives a clean foundation for future telemetry-driven provider selection.

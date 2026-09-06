# Week 2 — Day 12: Ollama Support — Local LLM Analysis (Private/Offline Mode)
**Date:** 2026-08-26
**Developer:** Aditya Gupta (Project Lead & LLM)
**Sprint:** SentinelAI 30-Day Sprint | Week 2, Day 12
**Status:** ✅ **COMPLETE**

---

## Day 12 Objective
> Add Ollama support — local Llama 3 via Ollama
> **Deliverable:** `analyze_scan_data(provider=LLMProvider.OLLAMA)` runs the full scan-analysis pipeline against a local Ollama server — no API key, no cloud, full privacy

---

## What Was Done

### 1. Ollama Provider Implementation (`sentinelai/prompt_engine.py`)

The Day 11 provider abstraction made this a drop-in addition:

| Piece | Purpose |
|-------|---------|
| `_call_ollama(prompt, preferred_model, retries, timeout_s)` | POSTs to `{OLLAMA_HOST}/api/generate` with `stream=False`; parses `response`, `prompt_eval_count`, `eval_count`, `total_duration` |
| `check_ollama_server()` | Health check via `/api/tags`; raises an **actionable** error ("start `ollama serve`, pull a model") when unreachable |
| `list_ollama_models()` | Auto-detects installed models — works whatever is pulled (llama3, gemma4, ...) instead of hardcoding llama3 |
| `_ollama_model_candidates()` | Candidate order: explicit → `OLLAMA_MODEL` env → installed models → `DEFAULT_OLLAMA_MODELS`; a **404 advances to the next candidate** instead of failing |

Config: `OLLAMA_HOST` env override (default `http://localhost:11434`). Uses the
already-present `requests` dependency — **no new packages**. No API key required.

### 2. Provider-Aware Timeouts (bug found during live validation)
First run failed: the request inherited Gemini's 300 s timeout, but gemma4's
first-time model load (~9 GB from disk) exceeded it. Fixed by making
`analyze_scan_data(timeout_ms=None)` resolve a **provider-aware default**:
300 s for Gemini, **600 s for Ollama**. After load, generation is GPU-fast.

### 3. Tests (`tests/test_prompt_engine.py`)
Replaced the Day 11 `NotImplementedError` guard with real behavior tests
(mock-based, still fully offline):
- Unreachable server → clear "Cannot reach Ollama server" RuntimeError
- `/api/generate` response parsing → model/text/usage verified end-to-end via
  the unified `analyze_scan_data()` entry point
- Missing-model 404 → falls through llama3 → succeeds on next candidate

```
$ python tests/test_prompt_engine.py
ALL prompt_engine TESTS PASSED (offline, pure functions)
```

### 4. Live Validation Wrapper (`test_day12_ollama_support.py`)
Resume-safe: server check → tiny smoke prompt → full localhost analysis.

---

## Test Results ✅ (Live, Local)

```
[+] Ollama server reachable at localhost
[+] Installed models: ['gemma4:latest']
[+] Smoke OK via gemma4:latest in 43.6s (tokens in=735, out=1620)
[+] Saved day12_analysis_localhost.md (6809 bytes)
```

`day12_analysis_localhost.md` contains **all 5 required sections**
(Summary / ranked Risk Findings / Attacker Perspective / Next Steps /
Confidence & Limitations) generated entirely locally — proving the
privacy/offline differentiator works.

---

## Integration Flow (Day 12)

```
scan JSON ──> build_prompt(mode) ──> analyze_scan_data(provider=OLLAMA)
                                           ↓
                    check_ollama_server() + list_ollama_models()
                                           ↓
                    POST {OLLAMA_HOST}/api/generate (stream=False)
                                           ↓
              day12_analysis_localhost.md  ← same quality bar as Gemini,
                                             zero cloud dependency
```

---

## Ready for Next Step

- **Day 13:** LLM switcher — `--llm openai/claude/gemini/ollama` flag; Gemini +
  Ollama dispatch already share one entry point, so this is CLI plumbing only
- **Day 14:** Team demo of the full pipeline

---

## Sign-Off

**Day 12 Status:** ✅ **COMPLETE AND VALIDATED**

- ✅ Ollama provider wired into unified entry point (no API key, no cloud)
- ✅ Auto-detects installed models; actionable errors when server is down
- ✅ Provider-aware timeout default fixed after live testing
- ✅ Offline unit tests + live gemma4 validation both passing

**Developer:** Aditya Gupta
**Completion Date:** 2026-08-26
**Team:** Team Finatics | CodeQuest 4.0
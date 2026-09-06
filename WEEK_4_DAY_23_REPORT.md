# Week 4 — Day 23: LLM Review Fixes — Prompt Edge Cases & API Error Handling
**Date:** 2026-09-05
**Developer:** Aditya Gupta (Project Lead & LLM)
**Sprint:** SentinelAI 30-Day Sprint | Week 4, Day 23
**Status:** ✅ **COMPLETE** (validated live + full offline suite green)

---

## Day 23 Objective
> Week 4 plan — Day 23: **"Fix any LLM-related bugs found in review — prompt
> edge cases, API errors."**
>
> **Goal:** the LLM module (`prompt_engine.py` + the CLI paths that reach it)
> is bug-free and handles errors gracefully: no wasted calls, no empty
> reports, no cryptic tracebacks, and both CLI entry points behave identically.

---

## Code-Review Findings & Fixes

| # | Finding (severity) | Symptom | Root cause | Fix |
|---|--------------------|---------|------------|-----|
| 1 | **Retired default Gemini model tried first** (🔴) | Every Gemini analysis attempted `gemini-2.0-flash` → 404, then fell back (slow, noisy) | `DEFAULT_MODEL_BY_PROVIDER[GEMINI]` still held the Day-10-retired name and sat **first** in the unified `_call_gemini` chain | Pointed the base at the live `gemini-flash-latest` alias; the rest of the chain is the known-good `DEFAULT_GEMINI_MODELS` |
| 2 | **`--model` ignored on the Gemini path** (🔴) | `--model X` had no effect; preferred model was never tried first | `_call_gemini` looped over `default_models_for_provider()` with a dead `if preferred_model: pass` block | Switched to `_model_candidates(preferred_model)` (preferred → env → defaults), matching `generate_nmap_analysis` |
| 3 | **Empty response saved as blank report** (🟠) | Safety-blocked / empty generation produced a 0-byte Markdown file | `response.text` was returned/ saved unguarded | Empty/None text now raises a clear error inside the loop → treated as non-retryable → next candidate is tried |
| 4 | **`usage_metadata` accessed unguarded** (🟠) | AttributeError on older SDKs could balloon into spurious retries + "All attempts failed" | Direct attribute access | `getattr(response, "usage_metadata", None)` |
| 5 | **UTF-8 BOM hard-fail** (🟠) | Windows writers (`Out-File`, Event Viewer, Notepad) prepend a BOM; `json.load`/CSV read crashed | Strict `utf-8` decode in `load_scan_data`, `load_event_log_data`, `log_parser.parse_logs` | `utf-8-sig` (BOM-aware) everywhere |
| 6 | **Malformed event-log JSON → confusing prompt** (🟠) | `analyze --kind events` with a list / wrong shape built a nonsense prompt | No schema validation | `build_event_log_prompt` now fails fast with actionable guidance (`parse --logs`, `logs -o events.json`) |
| 7 | **Root CLI `analyze` drifted** (🟠) | Root `sentinelai.py` `analyze` lacked `--routing` + raw-export auto-parse (`--llm` default differed) | The Week-2 "duplicate entry points" debt (working.md §Challenge 2) left untended | `commands/analyze.py` synced to `sentinelai/cli.py` — same options, same routing, same auto-parse; locked by a new sync test |
| 8 | **Non-JSON Ollama response → traceback** (🟡) | A proxy/HTML body crashed `resp.json()` uncaught | No decode guard | Wrapped in try/except ValueError → clean "non-JSON response" message, candidate skipped |
| 9 | **Stale "(soon) Ollama" wording** (🟡) | `analyze_scan_data` fallback said Ollama was still pending | Not updated after Day 12 | Corrected to "Gemini and Ollama are supported." |

---

## Validation

### Offline suite (all green)
```
$ py tests/test_prompt_engine.py   # ALL PASSED (incl. 6 new Day 23 tests)
$ py tests/test_cli_sync.py        # ALL 3 PASSED (new — analyze entry points identical)
$ py tests/test_routing.py         # ALL 5 PASSED
$ py tests/test_log_parser.py      # ALL 8 PASSED
$ py tests/test_event_bridge.py    # ALL 5 PASSED
$ py test_day16_event_log_llm.py --self-test   # SELF-TEST OK
```

New tests added:
- `test_default_models_for_provider_gemini` — retired name absent, live alias present
- `test_call_gemini_prefers_requested_model` — preferred model tried first
- `test_call_gemini_skips_empty_response` — empty → advances to next candidate
- `test_call_gemini_all_empty_raises` — aggregated "All attempts failed" error
- `test_call_ollama_non_json_response_clean_error` — clean message, not traceback
- `test_build_event_log_prompt_rejects_bad_schema` — fast, clear failure
- `test_load_event_log_data_handles_utf8_bom` — BOM'd Windows files load fine
- `tests/test_cli_sync.py` (3) — both `analyze` entry points stay identical

### Live checks
- `analyze -i <malformed>.json --kind events` → `[!] Analysis failed: Expected
  Windows event-log schema JSON (an object with an 'events' list)…` (graceful).
- **Live Ollama run**: `logs --sample --analyze --llm ollama` → full **5/5
  sections**, `POST /api/generate 200`, **`truncated = 0`** (no cut-off —
  the Day-15 `num_ctx` fix still holds end-to-end).

---

## Files Changed
| File | Change |
|------|--------|
| `sentinelai/prompt_engine.py` | Fixes #1–#4, #6, #9 + UTF-8 BOM (#5) in the JSON loaders |
| `sentinelai/log_parser.py` | `utf-8-sig` CSV read (#5) |
| `commands/analyze.py` | Synced to unified CLI (#7) |
| `tests/test_prompt_engine.py` | Updated + 7 new tests |
| `tests/test_cli_sync.py` | New (3 tests) |

---

## Sign-Off
**Day 23 Status:** ✅ **COMPLETE** — LLM module handles prompt edge cases and
API errors gracefully, validated offline + live.

**Developer:** Aditya Gupta | **Team:** Team Finatics | **CodeQuest 4.0**
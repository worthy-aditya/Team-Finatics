# Week 2 — Day 13: LLM Switcher (`--llm` flag)
**Date:** 2026-08-26
**Developer:** Aditya Gupta (Project Lead & LLM)
**Sprint:** SentinelAI 30-Day Sprint | Week 2, Day 13
**Status:** ✅ **COMPLETE**

---

## Day 13 Objective
> Build the LLM switcher — `--llm openai/claude/gemini/ollama` flag
> **Scope note (team decision):** only **gemini** and **ollama** are active — both free. The switcher accepts all four names; openai/claude fail with a friendly "paid API, not wired up yet" message until a later sprint day.

---

## What Was Done

### 1. Switcher Flag on the `analyze` Command
Both CLI entry points updated identically (`sentinelai/cli.py`, `commands/analyze.py`):

```
python sentinelai.py analyze -i scan_results.json --llm ollama
python sentinelai.py analyze --llm gemini --model gemini-3.6-flash
```

- `--llm [gemini|ollama|openai|claude]` — case-insensitive Click choice, default `gemini`
- `--model` help text is now provider-aware ("Preferred model for the chosen provider")
- Status lines echo the chosen provider before running

### 2. Provider Resolution (`sentinelai/prompt_engine.py`)
- **`resolve_provider(name)`** maps strings → `LLMProvider`:
  - `gemini` / `ollama` → active FREE providers ✅
  - `openai` / `claude` → `RuntimeError`: *"not wired up yet (paid API, planned for a later sprint day). Currently available FREE providers: gemini, ollama."*
  - unknown names → clear "Unknown LLM provider" error listing valid options
- `ACTIVE_PROVIDERS` constant documents what's live today

### 3. Unified File Flow + Bug Fix
- `analyze_scan_file(provider=...)` now routes through the unified
  `analyze_scan_data()` (single code path for every provider); saved files
  carry a new header: `Provider: ollama | Model: \`gemma4:latest\``
- 🐛 Fixed latent bug: the old `return model, analysis` sat **inside** the
  `if output_file:` block, so `--no-save` returned `None`. Return moved out.

### 4. Tests (`tests/test_prompt_engine.py`)
New offline unit tests: free-path mapping (incl. case/whitespace), paid-pending
refusals for openai/claude with guidance text, unknown-name error.

---

## Test Results ✅

Offline suite:
```
$ python tests/test_prompt_engine.py
ALL prompt_engine TESTS PASSED (offline, pure functions)
```

CLI help shows the switcher:
```
--llm [gemini|ollama|openai|claude]   LLM provider (free: gemini, ollama)  [default: gemini]
```

Paid-provider refusal (instant):
```
$ python sentinelai.py analyze --llm openai --no-save
[!] Analysis failed: LLM provider 'openai' is not wired up yet (paid API,
    planned for a later sprint day). Currently available FREE providers:
    gemini, ollama.
```

Live end-to-end via the local (free) provider:
```
$ python sentinelai.py analyze -i scan_results.json --llm ollama -o day13_analysis_ollama.md
[+] LLM analysis generated via ollama with gemma4:latest
[+] Saved analysis to day13_analysis_ollama.md      ← 7406 bytes, all 5 sections
```

---

## Integration Flow (Day 13)

```
--llm <name> ──> resolve_provider()  ──> gemini/ollama → analyze_scan_data()
                                      └─> openai/claude → friendly pending error
analyze_scan_file(provider=...) saves Markdown with Provider|Model header
```

---

## Ready for Next Step

- **Day 14:** Team sync — full demo of scan → LLM pipeline (both providers demoable)

---

## Sign-Off

**Day 13 Status:** ✅ **COMPLETE AND VALIDATED**

- ✅ `--llm` switcher live in both CLI entry points (free providers active)
- ✅ Friendly refusal for paid providers; unknown-name guidance
- ✅ Single unified code path for all providers; no-save bug fixed
- ✅ Offline tests + live ollama run passing

**Developer:** Aditya Gupta
**Completion Date:** 2026-08-26
**Team:** Team Finatics | CodeQuest 4.0
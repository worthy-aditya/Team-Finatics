# Week 5 — Day 36 Report (Feature Sprint)

**Date:** 2026-09-10
**Owner:** Aditya Gupta (Project Lead — AI/LLM Integration)
**Branch:** `aditya-dev` (Day 36 onward; Feature Sprint work merged here via `b6b10c4`)
**Plan task (Day 36):** Test the new prompt against sample/mock ZAP-style findings
**Status:** ✅ COMPLETE — **live LLM run PASSED**: Gemini returned a plain-English explanation of the mock findings; all harness quality checks green (offline + live); 124/124 regression

---

## 1. Deliverable

The Day 35 ZAP prompt template v1 was tested end-to-end against mock ZAP-style
findings (`day35_sample_zap_findings.json`, 3 alerts: SQL Injection / CSP
missing / X-Frame-Options missing) **through the real unified LLM pipeline**, and
the LLM returned a validated plain-English explanation:

```
$ python tests/test_day36_zap_prompt_llm.py --live --provider gemini --force
  live run: 3 mock alerts via gemini (free providers can take 1-2 minutes)...
  saved: day36_analysis_zap.md (8446 chars via gemini-3.6-flash)
  live quality checks PASSED (5 sections, alerts explained, no fabricated plugin IDs)
Day 36 ZAP PROMPT TEST: PASSED
```

Artifact: **`day36_analysis_zap.md`** — `Provider: gemini | Model: gemini-3.6-flash`.

## 2. What was built

| File | Change |
|---|---|
| `sentinelai/prompt_engine.py` | Day 36 pipeline: `load_zap_findings()` (BOM-aware, actionable errors), `analyze_zap_findings_data()` (mirrors `analyze_event_log_data()`: gemini + ollama, provider-aware timeouts, retry/backoff), `analyze_zap_file()` (file→Markdown artifact) |
| `tests/test_day36_zap_prompt_llm.py` | **NEW** — Day 16-style harness: `--self-test` (offline, mocked provider call) + `--live --provider gemini\|ollama` (resume-safe `--force`, `--suffix` artifacts) + programmatic quality checks |
| `day36_analysis_zap.md` | **NEW** — the live Gemini analysis of the mock findings (the deliverable proof) |

## 3. Harness quality checks (ground truth in the harness, never the prompt)

1. **Five-section contract** — exactly the Day 35 headings, in order
2. **Every input alert explained** — each alert `name` appears with a
   "Why it matters" plain-English explanation
3. **No-fabrication guard** — only plugin IDs present in the input may be cited
   (regex-scan of the analysis vs the input's allowed set)
4. **Ranked structure** — `Finding #1 -` present in section 2
5. Runs offline (`--self-test`, mocked `_call_gemini`) and live (`--live`)

## 4. Live-run quality notes (what Gemini actually produced)

- All 5 sections in order; each finding carries ZAP-native fields
  (plugin_id, risk, confidence, param, attack/evidence quoted exactly, CWE,
  OWASP tag from the input)
- **True-Positive Assessment done right:** header checks (CSP/X-Frame-Options)
  classified *near-certain true positives*; SQL Injection flagged as *suspected*
  (High risk / Medium confidence) needing manual confirmation — exactly the
  Day 35 distinction
- Verification steps are **safe and read-only** (browser dev-tools header
  inspection) — no new payloads
- No-fabrication guard: only plugin IDs 40018/10038/10020 cited

## 5. Validation

```
python tests/test_day36_zap_prompt_llm.py --self-test   → PASSED (3 mock alerts validated)
python tests/test_day36_zap_prompt_llm.py --live --provider gemini --force → PASSED
pytest 14 suites (day36 harness, zap_prompt, prompt_engine, active_gate
       offline+live, domain_verify offline+live, consent, cli_sync, ui,
       routing, log_parser, event_bridge, mapping)  → 124 passed
```

## 6. How to reproduce

```powershell
# offline (no key, no network)
python tests/test_day36_zap_prompt_llm.py --self-test
# live (needs GEMINI_API_KEY in .env, or --provider ollama with Ollama running)
python tests/test_day36_zap_prompt_llm.py --live --provider gemini
```

## 7. Scope / next (Day 37)

Per plan: *"Team sync — demo consent gate + domain verification end-to-end."*
Day 37 is the live authorization-flow demo (Day 34 `--active` gate against the
local lab server); the demo script is `WEEK_5_DAY_34_REPORT.md` §6 plus
`DAYS_30_35_SUMMARY.md` Step 3c. Next code day (Day 38) is Affan's ZAP
execution track integration + prompt refinements.

---

**Commit-ready files:** `sentinelai/prompt_engine.py`,
`tests/test_day36_zap_prompt_llm.py`, `day36_analysis_zap.md`

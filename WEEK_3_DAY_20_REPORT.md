# Week 3 — Day 20: Formal Cross-Provider Quality Comparison (Ollama `gemma4` vs Gemini `3.6-flash`)
**Date:** 2026-08-29
**Developer:** Aditya Gupta (Project Lead & LLM)
**Sprint:** SentinelAI 30-Day Sprint | Week 3, Day 20
**Status:** ✅ **COMPLETE** (matrix validated)

---

## Day 20 Objective
> Flagged since Day 18/19: *"Day 20: formal gemini vs ollama cross-provider
> comparison — regenerate all scenarios on both free providers and diff
> PASS/WARN/FAIL tables."*
>
> **Goal:** run a **16-cell matrix** — 4 scenarios × {standard, remediation} ×
> {ollama `gemma4:latest`, gemini `gemini-3.6-flash`} — validate every cell
> through the Day 16/17 harness, diff the quality checks, and turn the findings
> into a provider recommendation.

### Providers compared (both free tier)
| Provider | Model | Hosting | Data |
|----------|-------|---------|------|
| Ollama | `gemma4:latest` (3.2 GB, GPU) | Local | never leaves the machine |
| Gemini | `gemini-3.6-flash` | Cloud free tier | sent to Google API |

---

## What Was Run

### 1. The 16-cell matrix (4 scenarios x 2 modes x 2 providers)
Scenarios: **benign** (routine logons), **bruteforce** (RDP spray + lockout),
**incident** (`day15_sample_events.json` — backdoor + log clear), **real**
(`day19_parsed_events.json` — the real `--logs` parser output from Day 19).

### 2. Cells generated today (the missing ones)
- **gemini:** `incident` remediation, `real` standard + remediation, and a
  regenerated remediation trio (benign/bruteforce/incident) via
  `test_day16_event_log_llm.py --remediation --suffix gemini`.
- **ollama:** `incident` remediation (missing since Day 17).
- Representative wall-clock: gemini calls **~40–53 s** each; ollama incident
  remediation **~109 s** (including one transient Ollama **HTTP 500** that
  auto-retried and recovered).

### 3. `day20_compare.py` — reusable offline matrix generator
Re-runs the harness `check_analysis` over every saved output for both providers
and writes `day20_provider_comparison.md`.

---

## The Matrix (final)

| # | Mode | Scenario | Provider | Status | Sections | Invented IDs | Posture | Findings | Bytes |
|---|------|----------|----------|--------|----------|--------------|---------|----------|-------|
| 1 | standard | benign | ollama | ✅ PASS | 5/5 | ✅ none | ✅ low | 4 | 7452 |
| 2 | standard | benign | gemini | ✅ PASS | 5/5 | ✅ none | ✅ low | 16 | 7885 |
| 3 | standard | bruteforce | ollama | ✅ PASS | 5/5 | ✅ none | ✅ high | 5 | 8855 |
| 4 | standard | bruteforce | gemini | ✅ PASS | 5/5 | ✅ none | ✅ high | 12 | 9337 |
| 5 | standard | incident | ollama | ✅ PASS | 5/5 | ✅ none | ✅ critical | 5 | 9381 |
| 6 | standard | incident | gemini | ✅ PASS | 5/5 | ✅ none | ✅ critical | 17 | 9133 |
| 7 | standard | real | ollama | ✅ PASS | 5/5 | ✅ none | ✅ critical | 8 | 10221 |
| 8 | standard | real | gemini | ✅ PASS | 5/5 | ✅ none | ✅ critical | 20 | 10238 |
| 9 | remediation | benign | ollama | ✅ PASS | 4/4 | ✅ none | INFO | 4 | 5306 |
| 10 | remediation | benign | gemini | ✅ PASS | 4/4 | ✅ none | INFO | 6 | 4253 |
| 11 | remediation | bruteforce | ollama | ⚠ WARN | 4/4 | ⚠ **1102** | INFO | 13 | 5561 |
| 12 | remediation | bruteforce | gemini | ✅ PASS | 4/4 | ✅ none* | INFO | 8 | 5658 |
| 13 | remediation | incident | ollama | ✅ PASS | 4/4 | ✅ none | INFO | 3 | 4694 |
| 14 | remediation | incident | gemini | ✅ PASS | 4/4 | ✅ none | INFO | 8 | 5832 |
| 15 | remediation | real | ollama | ✅ PASS | 4/4 | ✅ none | INFO | 4 | 6341 |
| 16 | remediation | real | gemini | ✅ PASS | 4/4 | ✅ none | INFO | 12 | 7448 |

**Aggregates:** ollama **7 PASS / 1 WARN / 0 FAIL** · gemini **8 PASS / 0 WARN / 0 FAIL**.

*Row 12 originally WARN for `3389` — see the hardening below. After the fix it is
a clean PASS because `3389` is the **RDP port**, not a fabricated Event ID.

---

## Key Finding: the single WARN, and what it taught us
Both providers were flagged on **bruteforce remediation** — but for different
reasons, which made a great honesty test:

- **Ollama** cited auxiliary **Event ID 1102** ("verify audit log not cleared")
  that is **not** in the bruteforce input → the no-fabrication guard correctly
  kept an honest **WARN for review** (the same documented Day 17 case).
- **Gemini** was flagged for **3389** — which is the **RDP port** mentioned in
  firewall advice, not an event ID. The guard's "any standalone 4-digit number"
  heuristic cannot distinguish a **port** from a **fabricated Event ID**.

### Day 20 validator hardening (new)
- Added `PORT_NUMBERS` (common TCP/UDP ports) to `hallucinated_event_ids()`.
- Ports are now skipped; genuine auxiliary Event IDs (1102) are **still** flagged;
  negated mentions are still honored.
- Extended the harness self-test with 2 new assertions (3389 ignored, 1102 kept).
- Net effect: gemini → clean **8/8 PASS**; ollama keeps its honest **1102 WARN**.

---

## Qualitative Comparison (both reached the same conclusions)
- **Analytic agreement:** on `incident` and `real`, both providers independently
  ranked **Event 1102 (audit log cleared) as top / Critical** and flagged the
  4720 backdoor account — the intended ground truth, with zero fabrication.
- **Detail:** gemini is ~2× more granular (avg **12.4** findings vs **5.8**;
  `real` standard 20 vs 8) at similar total size (avg **7473** vs **7226** B).
- **Actionability:** gemini remediation included concrete PowerShell
  (`Get-WinEvent`, `Get-LocalUser`, `Disable-LocalUser`) + CIS/NIST 800-53 refs;
  ollama gave solid but more prose-based guidance with fewer concrete commands.
- **Reliability:** gemini API stable; ollama had one transient HTTP 500
  (auto-retry recovered) — expected for a local server under load.
- **Privacy/cost:** ollama is local and zero-cost; gemini is cloud free tier and
  sends log content off-host.

---

## Conclusion & Recommendation
Both providers are production-viable on the free tier and PASS equally on all
standard scenarios. Choose by role:
- **gemini** — richer, analyst-facing artifacts and more concrete remediation
  commands (default for detailed reports).
- **ollama** — private/local, cost-free, sufficient for the structured
  pass/fail pipeline and any sensitive logs that must not leave the host.
- The **port-vs-event-ID** hardening is a durable validator improvement that
  makes future cross-provider runs cleaner.

---

## Regression
```
$ py tests/test_prompt_engine.py      # ALL prompt_engine TESTS PASSED (offline)
$ py tests/test_log_parser.py         # ALL 8 log_parser TESTS PASSED (offline)
$ py test_day16_event_log_llm.py --self-test   # SELF-TEST OK (incl. new port cases)
```

---

## Ready for Next Step
- **Day 21+:** auto-detect `parse --logs` output directly in `analyze --kind
  events`; optional native EVTX via `python-evtx`; a small provider-routing
  decision (gemini for reports / ollama for private runs); re-run the matrix on
  Affan's live parser output once it lands.

---

## Sign-Off
**Day 20 Status:** ✅ **COMPLETE AND VALIDATED**

- ✅ 16-cell cross-provider matrix (4 scenarios × 2 modes × 2 free providers)
- ✅ Both providers PASS all standard scenarios; identical analytic conclusions
  (1102 critical; 4720 backdoor)
- ✅ Discovered & fixed a validator false positive: port 3389 ≠ invented Event ID
- ✅ Ollama retains its honest `1102` WARN — guard still catches real fabrication
- ✅ `day20_compare.py` reusable matrix generator + `day20_provider_comparison.md`
- ✅ Regression green: unit tests + harness self-test

**Developer:** Aditya Gupta
**Completion Date:** 2026-08-29
**Team:** Team Finatics | CodeQuest 4.0
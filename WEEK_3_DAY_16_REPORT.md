# Week 3 — Day 16: Event Log → LLM Testing & Quality Checks
**Date:** 2026-08-28
**Developer:** Aditya Gupta (Project Lead & LLM)
**Sprint:** SentinelAI 30-Day Sprint | Week 3, Day 16
**Status:** ✅ **COMPLETE**

---

## Day 16 Objective
> Test the LLM on sample Event Log data
> **Deliverable:** Prove the Day 15 `EVENT_LOG_ANALYSIS_PROMPT` works across
> diverse scenarios — and that the model does NOT hallucinate. Add a repeatable
> validation harness with programmatic quality checks.

---

## What Was Built

### 1. Three Diverse Scenario Fixtures
| Scenario | File | Ground-truth risk | What tests it |
|----------|------|-------------------|----------------|
| benign | `day16_scenario_benign.json` | Low | Routine logons only — model must NOT invent an attack |
| bruteforce | `day16_scenario_bruteforce.json` | High | Overnight RDP brute force + 3 AM remote logon + explicit creds |
| incident | `day15_sample_events.json` (reused) | Critical | Audit log cleared + backdoor account created |

Ground truth severity lives ONLY in the harness, never in the JSON the model
sees — otherwise the test would leak the answer and prove nothing about honesty.

### 2. Validation Harness (`test_day16_event_log_llm.py`)
Resume-safe (reuses saved outputs, `--force` to re-run), provider flag
(`--provider ollama|gemini`), `--suffix` (keeps per-provider artifacts apart),
and `--self-test` (offline check of the checkers themselves). Per scenario it
checks:

- **Sections 5/5** — required Markdown headers present (else `FAIL`)
- **No-hallucination** — every standalone 4-digit number in the analysis body
  (sections 1–3) must be a known input Event ID or the current year. Advice in
  Next Steps and *negated* mentions ("no 4625 events") are correctly excluded.
- **Risk posture** — highest `Severity:` rating vs expected, flagging
  over/under-stating by 2+ levels.
- **Findings count** — informational.

### 3. Checker Refinements (found by the harness itself)
Iterating the harness against real output exposed three measurement bugs —
each fixed and locked in with `--self-test`:
1. **WARN overrode FAIL** (a missing section turned FAIL into WARN) → severity
   priority now FAIL > WARN > PASS.
2. **Severity adjectives counted as ratings** ("monitor this critical event")
   falsely flagged benign as overstated → now scans only actual `Severity:`
   rating lines.
3. **Audit-advice vs fabrication** — `bruteforce` referencing `4720/4728` in
   *Next Steps* ("check for account changes (e.g. 4720/4728)") is advice, not a
   claim → Next Steps excluded. And a *negated* mention ("no 4625 events") is
   the model correctly noting absence, not hallucinating.

---

## Test Results ✅

Offline suites:
```
$ python tests/test_prompt_engine.py
ALL prompt_engine TESTS PASSED (offline, pure functions)
$ python test_day16_event_log_llm.py --self-test
SELF-TEST OK - quality-check helpers behave as expected
```

### Live validation — Ollama / gemma4 (local, private)
| Scenario | Sections | Invented IDs | Severity | Expected | Verdict |
|----------|----------|--------------|----------|----------|---------|
| benign | 5/5 | none | Medium | Low | ✅ PASS |
| bruteforce | 5/5 | none | High | High | ✅ PASS |
| incident | 5/5 | none | Critical | Critical | ✅ PASS |

### Live validation — Gemini / gemma-3.6-flash (cloud free tier)
| Scenario | Sections | Invented IDs | Severity | Expected | Verdict |
|----------|----------|--------------|----------|----------|---------|
| benign | 5/5 | none | Info | Low | ✅ PASS |
| bruteforce | 5/5 | none | Critical | High | ✅ PASS |
| incident | 5/5 | none | Critical | Critical | ✅ PASS |

Both providers produced **all 5 required sections with zero fabricated Event
IDs** across every scenario, and each ranked risk correctly (gemma4 called the
routine day Medium because of `4672` admin logons; gemini called it Info — both
defensible). All outputs in `day16_analysis_*.md`.

### Day 16 Problem Observed: Gemini free-tier flakiness
`gemini-3.6-flash` intermittently returned **503 "high demand"**; the harness's
backoff/retry (5s → 10s) absorbed it and completed all three runs. The model
chain also 404'd on outdated names (`gemini-2.0-flash`, `gemini-3.5-flash`),
resolving cleanly to `gemini-3.6-flash`. Confirms the Day 11 fallback-chain and
Day 13 provider abstraction are doing their job — a good sign heading into the
Day 20 cross-provider comparison.

---

## Integration Flow (Day 16)

```
day16_scenario_{benign,bruteforce}.json / day15_sample_events.json
        │
        ▼  analyze_event_log_file(provider=gemini|ollama)
   day16_analysis_{scenario}[.gemini].md
        │
        ▼  test_day16_event_log_llm.py checks
   sections 5/5 · no invented Event IDs · risk posture
        ▼
   PASS/WARN/FAIL summary per scenario
```

---

## Ready for Next Step

- **Day 17:** Remediation prompt layer — add an event-log REMEDIATION mode that
  turns the Day 16 findings into a prioritized fix-it list
- **Day 18:** Affan's real `--logs` parser output slots into this same harness
  (schema already matches `day15_sample_events.json`)
- **Day 20:** Repeat this harness across gemini/ollama for the formal
  cross-provider quality comparison

---

## Sign-Off

**Day 16 Status:** ✅ **COMPLETE AND VALIDATED**

- ✅ 3 diverse event-log scenarios (benign / brute-force / incident) tested
- ✅ Repeatable, resume-safe validation harness with offline self-test
- ✅ Both FREE providers pass: 5/5 sections, zero fabricated Event IDs, correct
  risk posture across all 6 runs
- ✅ Harness bugs found & fixed (FAIL priority, severity-label scanning,
  audit-advice vs fabrication, negated references)
- 🔜 Ready to test Affan's real `--logs` output (Day 18) and compare formally
  across providers (Day 20)

**Developer:** Aditya Gupta
**Completion Date:** 2026-08-28
**Team:** Team Finatics | CodeQuest 4.0

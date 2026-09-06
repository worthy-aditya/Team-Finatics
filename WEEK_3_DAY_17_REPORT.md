# Week 3 — Day 17: Remediation Mode (Findings → Prioritized Fix-It List)
**Date:** 2026-08-29
**Developer:** Aditya Gupta (Project Lead & LLM)
**Sprint:** SentinelAI 30-Day Sprint | Week 3, Day 17
**Status:** ✅ **COMPLETE** (validated end-to-end)

---

## Day 17 Objective
> Extend the Day 16 event-log pipeline with a **REMEDIATION mode** that turns
> the ranked security findings into a prioritized, evidence-tied **fix-it plan**,
> and extend the Day 16 validation harness to check *remediation* output — not
> just analysis output. Generate a live sample and validate it.
>
> **Deliverable:** `PromptMode.REMEDIATION` template + CLI/scan routing +
> harness `--remediation` path + a live Ollama/gemma4 sample that passes the
> no-fabrication guard.

---

## What Was Built

### 1. Remediation template (`sentinelai/prompt_engine.py`)
A new event-log REMEDIATION prompt (mirroring the scan-remediation variant
added Day 16) that always emits **four** required sections and a per-finding
fix-card format the harness can parse:

- `## 1. Executive Summary` — one-paragraph impact + single biggest win.
- `## 2. Prioritized Action List` — `Priority N` blocks, each with
  `**Finding #N - <title> (Event IDs ...)**`, `Risk rating`, `Verify now:`,
  `Fix:` steps, and a `Reference:` line. Every Event ID referenced must exist
  in the input (the harness enforces this).
- `## 3. Compliance Cross-Check` — map each Finding # to a control family
  (Access Control, Least Privilege, Incident Response, etc.).
- `## 4. Verification Plan` — concrete checks to confirm each fix landed.

The same template is reused by **both** scan and event-log inputs (the routing
key is `mode`, not `kind`), so remediation is now uniform across data types.

### 2. Routing (`sentinelai/cli.py`, `commands/analyze.py`)
`--mode remediation` is wired through `resolve_provider` →
`analyze_event_log_file(..., mode=PromptMode.REMEDIATION)` and
`analyze_scan_file(..., mode=PromptMode.REMEDIATION)`. Event logs are selected
with `--kind events`.

### 3. Harness extension (`test_day16_event_log_llm.py`)
The Day 16 harness was generalized to validate remediation output as a first-
class mode, not a special case:

- `REMEDIATION_REQUIRED_SECTIONS` — the 4 remediation headers.
- `check_analysis(...)` now takes **optional** `expected_max` and
  `required_sections` (signatures stay backward compatible). When
  `expected_max is None` (remediation mode) the **Risk posture** check becomes
  `INFO N/A (remediation mode)` and the **Sections** check uses
  `REMEDIATION_REQUIRED_SECTIONS` instead of the standard 5.
- The **no-hallucination guard is reused verbatim** — fabrication is
  fabrication whether it appears in a *finding* or a *fix card*, so the same
  `hallucinated_event_ids()` scanner runs over remediation plans too.
- New `--remediation` flag selects `REMEDIATION_SCENARIOS` (same input logs,
  remediation outputs) and passes `mode=REMEDIATION`.

---

## Live Sample & Validation

### CLI-generated sample (live, Ollama / `gemma4:latest`, local)
```
py -m sentinelai.cli analyze --input day16_scenario_bruteforce.json --kind events --mode remediation --llm ollama --model gemma4:latest -o day17_remediation_bruteforce.md
```
Saved artifact: **`day17_remediation_bruteforce.md`** (RDP brute force → 7 events,
input IDs `{4624, 4625, 4648, 4672, 4740}`).

### Harness validation of the saved sample
```
sections 4/4          PASS
no invented Event IDs  PASS      (invented: [])
findings              INFO      6 Finding cards (all reference input Event IDs)
VERDICT               PASS
```

### Harness end-to-end (`--remediation --force`) on `gemma4:latest`
| Scenario | Sections | Invented IDs | Findings | Verdict |
|----------|----------|--------------|----------|---------|
| benign     | 4/4 | none | 4 | ✅ PASS |
| bruteforce | 4/4 | `1102` | 13 | ⚠️ WARN |

### The `1102` WARN — a guard limitation, not a fabrication
The harness-regenerated bruteforce plan referenced `1102` in the Verification
Plan: "Confirm that Event ID 1102 (Audit Log Cleared) has not occurred since the
initial collection window." `1102` (Audit Log Cleared) is a **genuine, canonical
Windows Security-Log event** — it is *correct* auxiliary verification guidance,
not a hallucination. The guard is intentionally conservative: it flags **any**
standalone 4-digit number not present in the input, because it cannot reliably
distinguish a real-but-unseen Windows event from an invented one. So `1102` is
correctly flagged for human review (it resolves green on inspection) and the
verdict stays `WARN` (not `FAIL`) — a missing *section* is the only `FAIL`.

### Regression
```
$ py tests/test_prompt_engine.py        # ALL prompt_engine TESTS PASSED
$ py test_day16_event_log_llm.py --self-test   # SELF-TEST OK
```

---

## How It All Fits Together
```
day16_scenario_{benign,bruteforce}.json / day15_sample_events.json
        │
        ▼  analyze_event_log_file(..., mode=REMEDIATION)
        ▼
day17_analysis_*_remediation.md  (or day17_remediation_bruteforce.md)
        │
        ▼  test_day16_event_log_llm.py --remediation
        ▼
   sections 4/4 · no invented Event IDs · (no severity axis)
        ▼
   PASS / WARN(review) / FAIL
```

---

## Day 17 Open Items / Limitations
- **Conservative number scanner**: legit auxiliary Windows event IDs absent
  from the input (e.g. `1102`) trip the no-hallucination check. Acceptable for
  now; a future refinement could allowlist canonical Windows Security-Log IDs.
- **Ollama single-model**: only `gemma4:latest` was evaluated. The Day 20
  cross-provider comparison should re-run `--remediation` across providers.
- **Remediation has no severity axis**, so the harness treats risk posture as
  informational (`INFO`) for that mode — by design.

---

## Ready for Next Step
- **Day 18:** Affan's real `--logs` parser output slots into this same harness.
- **Day 20:** Repeat the `--remediation` validation across gemini/ollama.

---

## Sign-Off
**Day 17 Status:** ✅ **COMPLETE AND VALIDATED**

- ✅ `PromptMode.REMEDIATION` template for event logs (4-section plan + fix cards)
- ✅ CLI/scan routing confirmed (`--mode remediation --kind events`)
- ✅ Day 16 harness generalized to validate remediation (sections + reused
  no-fabrication guard), backward compatible, `--self-test` green
- ✅ Live Ollama/gemma4 sample produced and validated
- ✅ End-to-end `--remediation` path runs clean; benign PASS, bruteforce WARN
  (conservative-guard true-positive surfaced for review)
- ✅ Regression green: existing unit tests + harness self-test

**Developer:** Aditya Gupta
**Completion Date:** 2026-08-29
**Team:** Team Finatics | CodeQuest 4.0
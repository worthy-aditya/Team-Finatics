# Week 3 — Day 19: Land the Real `--logs` Parser and Run the Full Raw→Report Chain
**Date:** 2026-08-29
**Developer:** Aditya Gupta (Project Lead & LLM)
**Sprint:** SentinelAI 30-Day Sprint | Week 3, Day 19
**Status:** ✅ **COMPLETE** (end-to-end validated)

---

## Day 19 Objective
> Day 18 flagged today: **"Affan's `--logs` parser lands → drop-in"**. The Day 15
> engine already contains a stub note that *"Affan's `--logs` parser will feed
> structured event JSON here"* — but no parser existed in the repo. Day 17/18 used
> schema-identical fixtures as stand-ins.
>
> **Goal:** build the real `--logs` parser (`sentinelai parse`), convert a raw
> Windows event-log **CSV export** into the exact schema the analysis/remediation
> pipeline consumes, then validate the *entire* chain — raw CSV → parsed JSON →
> LLM standard report + remediation plan → harness checks.

---

## What Was Built

### 1. `sentinelai/log_parser.py` — the real parser (new module)
- **Input:** Windows Event Log CSV exports (the format produced by
  `wevtutil qe Security /f:csv` or Event Viewer "Save All Events As → CSV").
  Header columns are matched **by name** (order-independent, case-insensitive),
  so `Event ID` / `EventId` / `Event ID` all work regardless of column order.
- **EVTX path:** binary `.evtx` files are routed to the optional `python-evtx`
  package with a clear install hint; the CSV path never pays for that dependency.
- **Schema:** emits exactly the keys the Day 15/16/17 harness expects
  (`source`, `host`, `collected_at`, `window_start`, `window_end`, `count`,
  `events[].{event_id,timestamp,level,channel,account,domain,logon_type,
  logon_type_name,source_ip,source_host,message,count}`).
- **Enrichment + fallback extraction:**
  - `SECURITY_EVENT_META` fills in canonical level + default message for known
    Security IDs (4624/4625/4648/4672/4720/1102/…).
  - When a sparse export omits columns, `Account`, `Source IP`, and `Logon Type`
    are still recovered from the message text (`Target Account:`, IP literals,
    `Logon Type: N`).
  - Levels are normalized to **canonical strings** (`warning`, `information`,
    `critical`, …) so parsed output stays schema-consistent with the fixtures.
- **Tests:** `tests/test_log_parser.py` — 8 pure-function tests (schema shape,
  order-independent column detection, message fallback, level normalization,
  unknown-ID passthrough, empty-CSV guard, file round-trip). No pytest required.

### 2. `sentinelai parse` subcommand (new CLI)
```
sentinelai parse -i day19_sample_export.csv --logs -o day19_parsed_events.json --host CORP-LOGS
```
`--host` overrides the inferred source hostname; output is the drop-in JSON for
`sentinelai analyze --kind events`.

### 3. Realistic raw export — `day19_sample_export.csv`
A `wevtutil`-style CSV recreating the Day 18 incident: recon (4625) → explicit
credentials (4648) → lateral movement (4624) → privilege (4672) → data access
(5145/4663) → persistence backdoor (4720) → anti-forensics log clear (1102),
all from compromised source `10.0.5.23`.

> **Lesson learned on input size:** the first CSV used verbose full `<Event>`
> message text. gemma4's 6144-token context thrashed and produced no output after
> ~15 minutes (`ollama stop gemma4:latest` had to abort it). Regenerating the CSV
> with **concise, flat-text messages** — while keeping the same 9 Event IDs and
> source IP — let the same pipeline complete in a few minutes. Practical parser
> guidance: keep export messages trimmed, not full XML blobs.

---

## The Full Chain That Ran

```
day19_sample_export.csv          (raw wevtutil/Event-Viewer CSV export)
        ▼  sentinelai parse --logs  ──>  day19_parsed_events.json (9 events)
        ▼  sentinelai analyze --kind events
        ▼                               day19_analysis_real.md   (standard, 5 sections)
        ▼  sentinelai analyze --kind events --mode remediation
        ▼                               day19_remediation_real.md (4 sections)
        ▼  test_day16_event_log_llm.py check_analysis(...)
        ▼   sections · no-invented-ID · posture → PASS/PASS
```

---

## Validation Results ✅ (via the Day 16/17 harness)

| Artifact | Mode | Sections | Invented IDs | Severity / posture | Findings | Verdict |
|----------|------|----------|--------------|--------------------|----------|---------|
| `day19_analysis_real.md` | standard | 5/5 ✅ | none ✅ | critical = critical ✅ | 8 | ✅ **PASS** |
| `day19_remediation_real.md` | remediation | 4/4 ✅ | none ✅ | INFO (no axis) | 4 | ✅ **PASS** |

The model correctly ranked **1102 (audit log cleared)** as Critical #1, with
4720 (backdoor account) High — matching the intended incident ground truth.
Auxiliary references stayed grounded in the 8 input Event IDs; no fabrication.

### Regression
```
$ py tests/test_prompt_engine.py     # ALL prompt_engine TESTS PASSED (offline)
$ py tests/test_log_parser.py        # ALL 8 log_parser TESTS PASSED (offline)
$ py test_day16_event_log_llm.py --self-test   # SELF-TEST OK
```

---

## Ready for Next Step
- **Day 20:** Formal **gemini vs ollama** cross-provider comparison — regenerate
  all scenarios on both free providers and diff PASS/WARN/FAIL tables. The parser
  means every run now starts from a **real export**, not a fixture.
- Post-Day-20: wire `parse --logs` directly into `analyze` as `--kind events`
  auto-detection, and (Affan) drop in EVTX native parsing once `python-evtx` is
  approved as a dependency.

---

## Sign-Off
**Day 19 Status:** ✅ **COMPLETE AND VALIDATED**

- ✅ Real `sentinelai/log_parser.py` + `sentinelai parse --logs` CLI subcommand
- ✅ Raw CSV → parsed JSON proven drop-in for the Day 15 engine schema
- ✅ Standard risk report + remediation plan generated from the *parsed* real log
- ✅ Both artifacts **PASS** all harness checks (sections, no-fabrication, posture)
- ✅ Documented input-size pitfall (full XML messages overflow gemma4 context) and
  the concise-message fix
- ✅ Regression green: prompt-engine tests, new parser tests, harness self-test

**Developer:** Aditya Gupta
**Completion Date:** 2026-08-29
**Team:** Team Finatics | CodeQuest 4.0
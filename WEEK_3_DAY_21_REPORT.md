# Week 3 — Day 21: Auto-Detect Raw Log Exports + Provider Routing in `analyze`
**Date:** 2026-08-31
**Developer:** Aditya Gupta (Project Lead & LLM)
**Sprint:** SentinelAI 30-Day Sprint | Week 3, Day 21
**Status:** ✅ **COMPLETE** (validated end-to-end)

---

## Day 21 Objective
> Day 20 flagged today: **"auto-detect `parse --logs` output directly in
> `analyze --kind events`; a small provider-routing decision (gemini for
> reports / ollama for private runs)."**
>
> **Goal:** let the operator skip the manual two-step chain and point
> `sentinelai analyze --kind events` at a **raw CSV/EVTX export** — the CLI
> auto-runs the real Day 19 parser and routes to the right provider via an
> explicit `--routing` policy. Prove it end-to-end and validate the outputs.

---

## What Was Built

### 1. `sentinelai/routing.py` (new module — pure, testable)
| Function | Purpose |
|----------|---------|
| `route_provider(llm, routing)` | Resolve effective provider: explicit `--llm` wins > `--routing` policy > default `gemini` (backward compatible) |
| `is_raw_log_export(path)` | True for `.csv` / `.evtx` (case-insensitive) |
| `load_event_input(path)` | Auto-parse raw exports via the Day 19 parser; JSON passthrough |
| `auto_parse_to_file(path)` | Parse a raw export to a temp JSON file so the existing engine file-interface is reused unchanged |

`ROUTING_PROVIDER = {"report": "gemini", "private": "ollama"}` embodies the
Day 20 conclusion: gemini for analyst-facing reports, ollama when log data must
not leave the host (zero cloud egress).

### 2. `sentinelai/cli.py` — `analyze` now auto-detects + routes
- `--routing report|private` option added (policy-based provider selection).
- `--llm` stays an explicit override (wins over routing) and now defaults to
  `None` so routing can pick.
- When `--kind events` receives a `.csv`/`.evtx`, the CLI prints
  `[*] Auto-parsed raw event-log export -> N events` and feeds the parsed JSON
  straight into the analysis pipeline — no separate `parse` invocation needed.

```
sentinelai analyze --input day19_sample_export.csv --kind events --routing private
sentinelai analyze --input day19_sample_export.csv --kind events --routing private --mode remediation
```

### 3. `tests/test_routing.py` (new — offline, pure functions)
5 tests: routing priority (explicit llm > policy > default), invalid-policy guard,
raw-export detection (case-insensitive), auto-parse round-trip (schema correct),
and temp-JSON auto-parse.

---

## End-to-End Proof (fresh runs, ollama via `--routing private`)

Both runs started from the **raw** `day19_sample_export.csv` (no manual parse):

```
[*] Analyzing event log file: day19_sample_export.csv
[*] LLM provider: ollama                                  <- --routing private
[*] Auto-parsed raw event-log export -> 9 events          <- auto-detect worked
```

| Artifact | Mode | Sections | Invented IDs | Posture | Findings | Verdict |
|----------|------|----------|--------------|---------|----------|---------|
| `day21_analysis_autodetect.md` | standard | 5/5 ✅ | none ✅ | critical ✅ | 12 | ✅ **PASS** |
| `day21_remediation_autodetect.md` | remediation | 4/4 ✅ | none ✅ | INFO | 5 | ✅ **PASS** |

Both validated through the Day 16/17 harness; the model again ranked **1102
(audit-log clear) Critical** and **4720 (backdoor account) High** with zero
fabrication.

> **Ops note:** running two `analyze` calls against Ollama **concurrently** made
> `gemma4` thrash (both hung with flat CPU). Killing both and re-running
> **sequentially** completed cleanly. Sequential local-model runs are the
> reliable pattern for Ollama on this box.

---

## Regression
```
$ py tests/test_routing.py        # ALL 5 routing TESTS PASSED (offline)
$ py tests/test_log_parser.py     # ALL 8 log_parser TESTS PASSED (offline)
$ py tests/test_prompt_engine.py  # ALL prompt_engine TESTS PASSED (offline)
$ py test_day16_event_log_llm.py --self-test   # SELF-TEST OK
$ py -c "py_compile..."           # compile OK (cli, routing, log_parser, prompt_engine)
```

---

## Ready for Next Step
- **Day 22+:** optional native EVTX via `python-evtx` once the dependency is
  approved; wire `--routing` into `natural_cli`; a config file for default
  provider/routing; re-run the Day 20 matrix on Affan's live parser output when
  it lands.

---

## Sign-Off
**Day 21 Status:** ✅ **COMPLETE AND VALIDATED**

- ✅ `sentinelai/routing.py` — pure routing + auto-detect helpers
- ✅ `analyze --kind events` accepts raw CSV/EVTX with zero extra steps
- ✅ `--routing report|private` selects provider per Day 20 guidance
- ✅ Both fresh end-to-end outputs (standard + remediation) **PASS** harness
- ✅ Sequential-Ollama ops note documented (concurrent calls thrash the model)
- ✅ Regression green: routing/log-parser/prompt-engine tests + harness self-test

**Developer:** Aditya Gupta
**Completion Date:** 2026-08-31
**Team:** Team Finatics | CodeQuest 4.0
# Week 3 — Day 15: Windows Event Log Prompt Template
**Date:** 2026-08-28
**Developer:** Aditya Gupta (Project Lead & LLM)
**Sprint:** SentinelAI 30-Day Sprint | Week 3, Day 15
**Status:** ✅ **COMPLETE**

---

## Day 15 Objective
> Design the prompt for Windows Event Log analysis
> **Deliverable:** A reusable `EVENT_LOG_ANALYSIS_PROMPT` template plus the
> full provider-agnostic flow (`load → build → analyze → Markdown`), mirroring
> the proven Week 2 Nmap pipeline so Week 3 event data slots in unchanged.

---

## What Was Built

### 1. Event Log Prompt Template (`sentinelai/prompt_engine.py`)
`EVENT_LOG_ANALYSIS_PROMPT` — a strict 5-section Markdown template driven by
Windows **Security** event data, with explicit anti-hallucination and
correlation rules:

| § | Section | Forces the model to produce |
|---|---------|------------------------------|
| 1 | Plain-English Summary | host, time window, event count, event IDs, overall picture |
| 2 | Security Events (ranked by risk) | `Event #N`, `Severity (X/10)`, exact evidence, count-aware ranking |
| 3 | What These Events Suggest | defensive-only inference + event correlation (e.g. 4625→4624, 4720+4672) + prove/not-prove |
| 4 | Recommended Next Steps | Immediate (investigation) + Medium-term (hardening), each tied to events |
| 5 | Confidence & Limitations | basis, degradation factors, what's not covered |

Event IDs the template is built to interpret: 1102 (audit log cleared), 4624
(logon), 4625 (failed logon), 4672 (special privileges), 4720 (user created),
4728 (member added to security group) — matching Affan's Day 16 filter target.

### 2. Event Log Flow (mirrors the Nmap pipeline)
- `load_event_log_data(path)` — friendly loader (`event_logs.json` default)
- `build_event_log_prompt(data, mode=STANDARD)` — formats event JSON into the
  template. BEGINNER/REMEDIATION raise a clear *"not built yet on Day 15"*
  error (they land Day 17/19), never silently reuse the Nmap templates.
- `analyze_event_log_data(...)` — provider-agnostic (gemini + ollama), same
  signature/timeout semantics as `analyze_scan_data`.
- `analyze_event_log_file(...)` — file → Markdown with `Provider|Model` header.

### 3. CLI `--kind scan|events` (both entry points)
`sentinelai/cli.py` **and** `commands/analyze.py` updated identically so the
existing `analyze` command serves either data kind:
```
python sentinelai.py analyze -i day15_sample_events.json --kind events -o day15_analysis_events.md --llm ollama
python sentinelai.py analyze --kind scan -i scan_results.json --llm gemini      # unchanged default
```

### 4. Sample Data Contract (`day15_sample_events.json`)
The exact JSON schema Affan's `--logs` parser must emit:
`{ "source", "host", "collected_at", "window_start", "window_end", "count",
"events": [{event_id, timestamp, level, channel, account, domain, logon_type,
logon_type_name, source_ip, source_host, message, count}] }`. Ships a realistic
Security-log sample (4624/4625×14/4672/4720/4728/1102) so the template is
testable **now**, before the real parser lands.

### 5. Tests (`tests/test_prompt_engine.py`)
New offline (pure-function, no network) tests:
- event-log prompt contains all 5 required section headers
- event data (IDs, accounts, host) embedded in the prompt
- BEGINNER/REMEDIATION raise "not built yet"
- `analyze_event_log_data(provider=OLLAMA)` routes through `/api/generate` and
  uses the event-log (not Nmap) template
- missing event-log file → friendly `FileNotFoundError`

---

## Test Results ✅

Offline suite (works both as script and once pytest lands):
```
$ python tests/test_prompt_engine.py
ALL prompt_engine TESTS PASSED (offline, pure functions)
```

### Day 15 Problem Found & Fixed: Local-model output truncation
Initial live runs returned only **4 of 5** sections — the analysis stopped
mid-sentence with a cut-off. Root cause (via a direct API probe):

```
eval_count: 2099 · done_reason: length   ← hit a token ceiling
```

gemma4's Ollama context window defaults to **4096 tokens TOTAL** (prompt +
output), so no matter how long the requested output, generation stops once
context runs out. Fixed in `_call_ollama` by raising both knobs —
`num_ctx` (default **6144**; 8192 is rejected by gemma4) and
`num_predict` (**4096**) — plus compacting the event JSON in the prompt
(separators, ~950 chars saved). All env-overridable
(`OLLAMA_NUM_CTX` / `OLLAMA_NUM_PREDICT`).

### Live validation (local, private — no wifi needed)
```
$ python sentinelai.py analyze -i day15_sample_events.json --kind events \
    -o day15_analysis_events.md --llm ollama
[+] LLM analysis generated via ollama with gemma4:latest
[+] Saved analysis to day15_analysis_events.md
```
`day15_analysis_events.md` (7.8 KB) contains **all 5 sections**, correctly
ranking the audit-log clear (1102) as Critical, correlating all suspicious
activity back to source IP `192.168.1.54`, and giving concrete investigation +
hardening steps.

---

## Integration Flow (Day 15)

```
Windows Security --logs (Affan, Days 15-17) / day15_sample_events.json
        │  structured JSON contract
        ▼
load_event_log_data() ──► build_event_log_prompt(mode=STANDARD)
        │
        ▼
analyze_event_log_data(provider=gemini|ollama)
        │            └─ _call_gemini() / _call_ollama(num_ctx=6144)
        ▼
day15_analysis_events.md  (Provider | Model header + 5 sections)
```

---

## Ready for Next Step

- **Day 16:** Event Log → LLM analysis testing (Affan's real `--logs` data feeds
  the pipeline; wire schema validation + integration test)
- **Day 17:** Remediation prompt layer (event-log REMEDIATION variant of this
  template)
- **Day 19:** Beginner mode for event logs (`--beginner`)

---

## Sign-Off

**Day 15 Status:** ✅ **COMPLETE AND VALIDATED**

- ✅ `EVENT_LOG_ANALYSIS_PROMPT` — evidence-based 5-section Windows Security
  log analysis template
- ✅ Full provider-agnostic flow (load → build → analyze → Markdown) + CLI
  `--kind events`
- ✅ Sample data contract for Affan's parser (`day15_sample_events.json`)
- ✅ Offline unit tests green
- ✅ Live Ollama run produced all 5 sections (truncation bug found & fixed)
- 🔜 Needs Affan's real `--logs` output to complete integration (Day 16)

**Developer:** Aditya Gupta
**Completion Date:** 2026-08-28
**Team:** Team Finatics | CodeQuest 4.0

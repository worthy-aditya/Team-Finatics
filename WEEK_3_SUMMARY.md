# Week 3 — Weekly Summary: Events, Remediation, Parser & Cross-Provider Validation
**Date:** 2026-08-31
**Author:** Aditya Gupta (Project Lead & LLM) — Team Finatics | CodeQuest 4.0
**Sprint:** SentinelAI 30-Day Sprint | Week 3 (Days 15–21)

---

## Overview
Week 3 extended SentinelAI from Nmap scanning (Week 2) into **Windows Security
Event Log analysis**: a prompt template, a validation harness, a remediation
mode, the real `--logs` parser, the Day 19/21 end-to-end chain, a formal
cross-provider comparison, and provider routing. Below is the per-day breakdown:

| Day | Theme | Outcome |
|-----|-------|---------|
| 15 | Event-log prompt template | ✅ 5-section template + provider-agnostic flow |
| 16 | Event-log → LLM testing & quality | ✅ Harness + 6 live runs, zero hallucination |
| 17 | Remediation mode | ✅ Findings → prioritized fix-it plan |
| 18 | Real-shaped event logs | ✅ Production-shaped fixture validated (PASS) |
| 19 | Real `--logs` parser | ✅ Raw CSV/EVTX → JSON → reports (PASS) |
| 20 | Cross-provider comparison | ✅ 16-cell matrix, validator hardened |
| 21 | Auto-detect + routing | ✅ Raw exports straight into `analyze` |

---

# Day 15 — Windows Event Log Prompt Template

- **Task:** Design the prompt that drives LLM analysis of Windows Event Logs and
  build the full flow around it.
- **Why necessary:** Week 2 already had a proven Nmap pipeline. Week 3 needed the
  same trusted path for Security event logs (the primary post-compromise
  evidence source) — otherwise every new data type would need bespoke code.
- **Objective:** A reusable `EVENT_LOG_ANALYSIS_PROMPT` (strict 5-section,
  evidence-based) plus `load → build → analyze → Markdown`, mirroring the Nmap
  flow so Affan's `--logs` data can slot in unchanged.
- **How completed:**
  - Built `EVENT_LOG_ANALYSIS_PROMPT` with 5 sections (Summary / Events ranked /
    What these suggest / Next steps / Confidence & Limitations) and explicit
    anti-hallucination + correlation rules for IDs 1102/4624/4625/4672/4720/4728.
  - Added `load_event_log_data`, `build_event_log_prompt`, `analyze_event_log_*`
    (provider-agnostic: gemini + ollama), and CLI `--kind scan|events` on both
    entry points.
  - Ships the schema contract `day15_sample_events.json` so the template is
    testable before the real parser lands.
  - Green offline unit tests (`tests/test_prompt_engine.py`).
- **Problems faced:** **Local-model output truncation.** Live runs returned only
  4 of 5 sections — `done_reason: length`. Root cause: gemma4's Ollama context
  defaulted to **4096 tokens TOTAL**, so generation stopped early. Fixed by
  raising `num_ctx` to 6144 and `num_predict` to 4096 (both env-overridable),
  plus compacting the event JSON in the prompt. All 5 sections then generated.

---

# Day 16 — Event Log → LLM Testing & Quality Checks

- **Task:** Prove the Day 15 prompt works across diverse scenarios **and** that
  the model doesn't hallucinate event IDs.
- **Why necessary:** A prompt that looks good in one example can still invent
  findings on unseen data. The team needed a repeatable, honest way to catch
  fabrication and wrong risk posture before trusting AI reports.
- **Objective:** A validation harness with 3 diverse scenario fixtures
  (benign / brute-force / incident) and programmatic quality checks; ground
  truth severity lives only in the harness, never in the prompt (so it can't be
  leaked or gamed).
- **How completed:**
  - `test_day16_event_log_llm.py` — resume-safe (`--force`), provider flag,
    `--suffix` for per-provider artifacts, offline `--self-test`, and checks:
    **5/5 sections**, **no-invented-Event-ID** guard, **risk posture** vs
    expected, findings count.
  - Ran it on **both free providers** — ollama/gemma4 and gemini/gemini-3.6-flash
    → all 6 runs **PASS** (5/5 sections, zero fabricated IDs).
- **Problems faced:**
  1. **Gemini free-tier flakiness** — intermittent 503 "high demand"; backoff
     retry absorbed it. Model chain 404s on renamed models resolved cleanly to
     `gemini-3.6-flash`.
  2. **Three harness measurement bugs** surfaced by iterating on real output:
     WARN was overriding FAIL; generic severity *adjectives* were counted as
     ratings; audit *advice* ("check for 4720/4728") and *negated* mentions
     ("no 4625") were misread as fabrication. Each fixed and locked in with
     `--self-test`.

---

# Day 17 — Remediation Mode (Findings → Prioritized Fix-It List)

- **Task:** Extend the event-log pipeline with a **REMEDIATION mode** that turns
  ranked findings into actionable fix-it plans, and teach the harness to
  validate remediation output (not just analysis).
- **Why necessary:** A risk report without a fix plan is half a product.
  Remediation = analysis findings + prioritized, evidence-tied remediation.
- **Objective:** `PromptMode.REMEDIATION` template + CLI routing + harness
  `--remediation` + a live, validated sample.
- **How completed:**
  - 4-section template: Executive Summary / Prioritized Action List (fix cards
    with Risk rating, Verify now, Fix, Reference) / Compliance Cross-Check /
    Verification Plan — reused for both scan and event-log inputs.
  - Generalized `check_analysis(...)` with optional `expected_max` and
    `required_sections`; reuse the same no-fabrication guard for fix cards.
  - Live ollama/gemma4 sample produced and validated; end-to-end benign →
    PASS, bruteforce → WARN.
- **Problems faced:** **The `1102` WARN — a guard limitation, not a fabrication.**
  The regenerated bruteforce plan suggested verifying that Event ID **1102**
  (Audit Log Cleared — a real Windows event) hadn't occurred. `1102` isn't in
  that scenario's input, so the intentionally-conservative guard flagged it for
  human review (WARN, not FAIL). It resolves green on inspection — a genuine
  "true positive for a false alarm" case, and the Day 20 follow-up explored
  distinguishing it correctly.

---

# Day 18 — Validate Affan's Real Event-Log Shape Through the Pipeline

- **Task:** Prove the analysis + remediation pipeline works on a **realistic,
  production-shaped** Windows event log from a genuine incident workflow — not a
  toy.
- **Why necessary:** Affan's real `--logs` parser isn't committed yet. To
  de-risk integration, the team needed to prove the *shape* of his parser output
  flows through end-to-end today.
- **Objective:** A schema-identical, production-shaped fixture run through both
  standard and remediation, validated by the Day 16/17 harness (drop-in
  replacement for the real parser).
- **How completed:**
  - `day18_sample_events.json` — a multi-event incident across
    WORKSTATION-23 → HOST-DB01 from one compromised IP (10.0.5.23): recon
    (4625) → explicit creds (4648) → lateral movement (4624) → privilege (4672)
    → data access (5145/4663) → persistence backdoor (4720) → anti-forensics
    log clear (1102). Same schema as `day15_sample_events.json`.
  - Ran standard + remediation on Ollama/gemma4 → **both PASS** the harness
    (5/5, 4/4 sections; no invented IDs; posture critical).
- **Problems faced:**
  - A noted **assumption**: real parser not in repo; fixture documented as a
    schema stand-in.
  - A subtle but desirable case: the model's Verification Plan referenced `1102`
    and `4720` — **both present in the input**, so the no-fabrication guard
    correctly let grounded auxiliary references through (the flip side of
    Day 17's WARN).

---

# Day 19 — Land the Real `--logs` Parser

- **Task:** Build the actual parser that converts raw Windows event-log exports
  into the pipeline's schema (`sentinelai parse --logs`).
- **Why necessary:** Until now every run used fixtures (Days 15, 17, 18). A real
  export must be able to go straight to analysis, so the toolchain is genuinely
  usable, not demo-only.
- **Objective:** `sentinelai/log_parser.py` + a `parse` CLI subcommand that
  takes CSV (and EVTX via optional `python-evtx`) → schema JSON; prove it by
  converting a realistic raw export and running standard + remediation.
- **How completed:**
  - Parser with **order-independent, case-insensitive** header detection,
    `SECURITY_EVENT_META` enrichment, message-text fallback (account / source IP
    / logon type), canonical level strings, EVTX hint, and temp-JSON output.
  - `sentinelai parse -i day19_sample_export.csv --logs -o day19_parsed_events.json`.
  - New `tests/test_log_parser.py` (8 offline tests).
  - Parse → analyze (standard + remediation) → **both PASS** harness.
- **Problems faced:**
  1. **Input bloat vs model context.** Verbose full `<Event>` XML messages blew
     gemma4's 6144-token window (stalled ~15 min, had to `ollama stop`).
     Switching to **concise flat-text messages** (same IDs/IP) let runs complete
     in minutes. Documented as parser guidance: keep messages trimmed.
  2. Account-regex captured a trailing period; fixed the character class.
  3. Level normalization was inconsistent (int vs string across paths); made
     levels canonical strings to stay schema-compatible.

---

# Day 20 — Formal Cross-Provider Quality Comparison

- **Task:** Run the 16-cell matrix (4 scenarios × {standard, remediation} ×
  {ollama, gemini}) and diff PASS/WARN/FAIL, then turn it into a provider
  recommendation.
- **Why necessary:** The team had no data-driven basis for which FREE provider
  to default to; decisions were anecdotal.
- **Objective:** A complete matrix, a reusable generator, and a clear
  recommendation.
- **How completed:**
  - Filled every missing cell (gemini remediation trio; gemini `real` std +
    remediation; ollama incident remediation).
  - `day20_compare.py` validates all saved outputs offline and writes
    `day20_provider_comparison.md`.
  - **Result:** ollama **7 PASS / 1 WARN / 0 FAIL**; gemini **8 PASS / 0 WARN /
    0 FAIL** after hardening. Both ranked 1102 critical; gemini ~2× more
    granular (avg 12.4 vs 5.8 findings); ollama private/zero-cost.
  - **Recommendation:** `report → gemini`, `private → ollama`.
- **Problems faced:**
  1. **Transient Ollama HTTP 500** on one call — auto-retry recovered.
  2. **A stuck gemini harness call** (flat CPU ~25 min) — killed the chain, ran
     each call **individually** (~40–53 s each) via a direct helper.
  3. **Validator false positive found:** gemini was flagged for `3389` — the
     **RDP port**, not a fabricated Event ID. Added a `PORT_NUMBERS` allowlist to
     the guard so ports are ignored while genuine auxiliary IDs (like the
     `1102` advice) are still flagged; self-test extended.

---

# Day 21 — Auto-Detect Raw Log Exports + Provider Routing

- **Task:** Let `analyze --kind events` accept a **raw CSV/EVTX export** directly
  (auto-run the Day 19 parser) and route the provider via policy.
- **Why necessary:** The Day 19-20 flow still required a manual `parse` step
  before `analyze`; the Day 20 recommendation (`report`→gemini,
  `private`→ollama) wasn't wired into the CLI.
- **Objective:** Skip the manual parse step; one command raw-export → LLM with
  data-privacy-aware provider selection.
- **How completed:**
  - `sentinelai/routing.py` — `route_provider` (explicit `--llm` > `--routing`
    > default), `is_raw_log_export`, `load_event_input`, `auto_parse_to_file`.
  - `analyze` now prints `[*] Auto-parsed raw event-log export -> N events`;
    new `--routing report|private` option.
  - `tests/test_routing.py` (5 offline tests).
  - End-to-end from **raw CSV** via `--routing private` → ollama: standard +
    remediation **both PASS** harness.
- **Problems faced:** Two **concurrent** Ollama `analyze` calls made gemma4
  thrash (both hung, flat CPU). Killing both and re-running **sequentially**
  completed cleanly — documented ops note: sequential local-model runs are the
  reliable pattern.

---

## Cross-Day Threads & Lessons

1. **A shared contract made the sprint parallel-safe.** The Day 15 schema
   (`day15_sample_events.json`) let fixtures (17/18), the real parser (19), and
   harness validation (16/17/20) all proceed without blocking on Affan.
2. **Keep the input light.** Two different stalls were both “too much content
   pushed through a local model” (Day 15 full templates, Day 19 verbose
   messages). Keep input tight; sequential calls on Ollama.
3. **No-fabrication guard is intentionally conservative** (Day 17 `1102` WARN),
   and Day 20+21 refined it precisely — grounded aux IDs pass if in input
   (Day 18), ports are excluded (Day 20), genuine absent-event-ID advice stays
   flagged for humans.
4. **Validation paid for itself:** the harness caught its own bugs (Day 16),
   model truncation (Day 15/19), and a port-vs-event-ID false positive
   (Day 20).

---

## Regression & State (end of Week 3)

```
$ py tests/test_routing.py        # ALL 5 routing TESTS PASSED
$ py tests/test_log_parser.py     # ALL 8 log_parser TESTS PASSED
$ py tests/test_prompt_engine.py  # ALL prompt_engine TESTS PASSED
$ py test_day16_event_log_llm.py --self-test   # SELF-TEST OK
```

**Week 3 Status:** ✅ **COMPLETE** — Day 15–21 objectives met and validated.

**Next (Week 4+):** EVTX native parsing (once `python-evtx` is approved),
`--routing` in `natural_cli`, config defaults, and re-running the matrix on
Affan's live parser output once it lands.

**Team:** Team Finatics | CodeQuest 4.0
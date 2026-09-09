# Week 5 — Day 35 Report (Feature Sprint)

**Date:** 2026-09-09
**Owner:** Aditya Gupta (Project Lead — AI/LLM Integration)
**Plan task (Day 35):** Design the LLM prompt template for explaining active-scan (ZAP) findings
**Status:** ✅ COMPLETE — template v1 drafted (13/13 offline tests; 123/123 full regression)

---

## 1. Deliverable

**`ZAP_ANALYSIS_PROMPT` — template v1** now lives in `sentinelai/prompt_engine.py`
alongside the Day 9/10 (Nmap) and Day 15 (Windows Event Log) templates, plus a
fail-fast builder (`build_zap_prompt()`) and a schema-contract fixture
(`day35_sample_zap_findings.json`) that Day 36's mock-findings test will feed to a
real LLM. No CLI/LLM wiring today — that lands with Day 36, per the plan split.

## 2. How v1 is DISTINCT from the scan/log templates (plan requirement)

| Dimension | Nmap (Day 9/10) | Event Log (Day 15) | **ZAP (Day 35, v1)** |
|---|---|---|---|
| Persona | network analyst | Windows security analyst | **web-application analyst** |
| Evidence unit | open port/service | Windows event ID | **ZAP alert** (plugin_id, risk, confidence, param, attack/evidence, CWE) |
| Ranking driver | port exposure | event count/frequency correlation | **risk first, then confidence; dedupe across URLs** |
| Section 3 | Attacker Perspective | What These Events Suggest | **True-Positive Assessment** — near-certain TP vs likely FP (Low-confidence config alerts), one safe read-only verification per top finding, what the scan proves / does not prove |
| Framework hook | NSE scripts for defenders | Windows guidance (CIS/NIST) | **OWASP Top 10 tags from the alert (or a marked "(proposed)" mapping) + CWE** |
| Payload safety | no exploit steps | no attack walkthrough | **only the attack/evidence strings ZAP itself reported may be referenced — never craft new payloads; re-tests are read-only checks** |

The five-section contract shape is kept (house style), but section semantics are
ZAP-native. Placeholder is `{zap_findings}` (compact JSON — Day 15 rationale:
payload is reference context; indenting wastes tokens).

## 3. Authorization tie-in (Days 31–34)

The template's defensive-framing block states explicitly that the findings come
from an **AUTHORIZED** active test: the two-layer gate (typed consent attestation +
`.well-known/sentinelai-verify.txt` token) ran before the scan. The schema fixture
carries an `authorized` block (`consent`, `domain_verified`, `audit_log`) so the
authorization provenance travels with the findings into every LLM analysis.

## 4. Schema contract v1 (`day35_sample_zap_findings.json`)

```
{source, target, scan_policy, scan_time,
 authorized: {consent, domain_verified, audit_log},
 count, alerts: [{plugin_id, name, risk, confidence, cwe_id, url, method,
                  param, attack, evidence, description, solution, reference,
                  tags{OWASP}}, ...]}
```
Only `alerts` is mandatory — an empty list is a valid **clean scan** (the template
handles it: "say the scan came back clean and what that does and does not
guarantee"). ZAP's JSON alert export maps onto these fields.

## 5. Builder behavior (Day 23 fail-fast convention)

- `build_zap_prompt(zap_findings, mode=STANDARD)` → formats v1 with compact JSON
- Non-dict / missing `alerts` → `ValueError` naming the schema + the fixture file
- Event-log-shaped input (`{"events": [...]}`) → rejected with the ZAP-specific
  message (never silently prompts with the wrong payload)
- `BEGINNER` / `REMEDIATION` → clear "not built yet" error (same convention as
  the Day 15 event-log builder; variants arrive on later sprint days)
- New constants: `DEFAULT_ZAP_INPUT_FILE = zap_findings.json`,
  `DEFAULT_ZAP_ANALYSIS_OUTPUT_FILE = day36_analysis_zap.md`

## 6. Validation

```
py_compile prompt_engine.py + tests/test_zap_prompt.py               → OK
python tests/test_zap_prompt.py                                      → 13/13 PASSED
pytest 13 suites (zap_prompt, prompt_engine, active_gate offline+live,
       domain_verify offline+live, consent, cli_sync, ui, routing,
       log_parser, event_bridge, mapping)                            → 123 passed
```

Test highlights: template ≠ both existing templates; exactly the five section
headings; `{zap_findings}` placeholder only; ZAP vocabulary present; authorized/
attestation/`sentinelai-verify.txt` framing present; fixture satisfies the
documented contract; builder accepts clean scans and rejects every malformed input.

## 7. Next (Day 36)

Per plan: *"Test the new prompt against sample/mock ZAP-style findings → LLM
returns plain-English explanation of a mock finding."* Day 36 wires
`load_zap_findings()` + an `analyze_zap_findings()` path through the unified
provider pipeline (gemini/ollama), runs the fixture through a live LLM, and
harness-checks the output for the five sections and no-fabrication rules.

---

**Commit-ready files:** `sentinelai/prompt_engine.py`,
`day35_sample_zap_findings.json`, `tests/test_zap_prompt.py`

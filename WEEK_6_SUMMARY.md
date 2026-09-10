# Week 6 — Sprint Summary & Feature-Verification Guide (Feature Sprint: ZAP + Findings)

**Project:** SentinelAI CLI · Team Finatics · CodeQuest 4.0
**Scope:** Week 6 of the Feature Sprint (Days 36–42) — completed so far: **Day 36 (ZAP prompt vs live LLM)** and **Day 37 (authorization-flow team demo)**
**Updated:** 2026-09-10 · branch **`aditya-dev`** @ Day 36+37 commits (all pushed)

This condenses `WEEK_5_DAY_36_REPORT.md` and `WEEK_5_DAY_37_REPORT.md` into one
page: **what was built**, then a **stepwise verification playbook** — exact
commands and exact expected output.

---

## Part 1 — What happened each day

### Day 36 — ZAP prompt tested against mock findings (LIVE LLM)
- **Task:** *"Test the new prompt against sample/mock ZAP-style findings."*
- **Delivered:** The Day 35 `ZAP_ANALYSIS_PROMPT` ran through the **real unified
  LLM pipeline** against the 3 mock alerts in `day35_sample_zap_findings.json`
  (SQL Injection / CSP missing / X-Frame-Options missing). A **live Gemini run**
  (`gemini-3.6-flash`, 8,446 chars) returned the full five-section plain-English
  explanation and passed every harness check.
- **New code:** `load_zap_findings()`, `analyze_zap_findings_data()`,
  `analyze_zap_file()` in `sentinelai/prompt_engine.py` (mirrors the event-log
  pipeline: gemini + ollama, provider-aware timeouts, BOM-aware loader,
  fail-fast schema errors).
- **New harness:** `tests/test_day36_zap_prompt_llm.py` — `--self-test` (offline,
  mocked provider), `--live --provider gemini|ollama` (resume-safe artifacts),
  and programmatic quality checks: five-section contract, every alert explained
  ("Why it matters"), **no-fabrication guard** (only input plugin IDs citable),
  ranked `Finding #1 -` structure.
- **Artifact:** `day36_analysis_zap.md` (committed).
- **Regression:** 124 passed across 14 suites.

### Day 37 — Team sync: authorization flow demoed end-to-end
- **Task:** *"Team sync — demo consent gate + domain verification end-to-end."*
- **Delivered:** `tests/demo_authorization_flow.py` — a **timed automated live
  demo rehearsal** (Day 27 conventions) with **zero mocks**: real CLI subprocess,
  real HTTP `.well-known` fetch, real nmap scan, real audit trail. **PASSED 6/6
  stages, 28.3 s / 180 s gate.**
- **The 6 stages:** preflight → token + `.well-known` publish + local server →
  **GRANT** (attestation typed → domain verified → nmap scan runs) → **DENY**
  (wrong token → `token_mismatch`, no scan) → **GUARD** (`--active --yes`
  rejected) → audit trail (`granted → verified → granted → denied` — every run
  attests fresh, by design).
- **Rehearsal catch:** the first run failed the audit stage because the deny run
  legitimately produces a fresh consent grant before the token mismatch — the
  record now documents that 4-record trail for the team.
- **Files:** `tests/demo_authorization_flow.py`, `WEEK_5_DAY_37_REPORT.md`.

### Upcoming (per plan)
- **Day 38–42** — Aditya: remediation per finding, risk-weighting (confirmed vs
  potential), LLM against **real** ZAP output (needs Affan's track), edge cases;
  Affan: ZAP active box in orchestrator, Juice Shop first real scan;
  Suraj: Authorization Record appendix in DOCX/PDF; Sneha: SECURITY.md, docs,
  full regression. **Day 43–44** — positioning doc + full demo narrative.

---

## Part 2 — Verify it yourself, step by step

Run from the repo root in PowerShell with the venv activated (or use
`.\venv\Scripts\python.exe` everywhere instead of `python`).

### Step 0 — Sanity

```powershell
git branch --show-current        # → aditya-dev
python sentinelai.py --version   # → SentinelAI, version 1.0.0
```

### Step 1 — Day 36: ZAP prompt vs mock findings

**1a. Offline self-test (no network, no key):**
```powershell
python tests/test_day36_zap_prompt_llm.py --self-test
```
→
```
  offline self-test OK (3 mock alerts validated)
Day 36 ZAP PROMPT TEST: PASSED
```

**1b. Live run (needs `GEMINI_API_KEY` in `.env`, or `--provider ollama` with
Ollama running):**
```powershell
python tests/test_day36_zap_prompt_llm.py --live --provider gemini --force
```
→
```
  live run: 3 mock alerts via gemini (free providers can take 1-2 minutes)...
  saved: day36_analysis_zap.md (8446 chars via gemini-3.6-flash)
  live quality checks PASSED (5 sections, alerts explained, no fabricated plugin IDs)
Day 36 ZAP PROMPT TEST: PASSED
```

**1c. The plain-English explanation it produced** — open `day36_analysis_zap.md`:
- **§1 Summary** — 3 alerts (1 High / 1 Medium / 1 Low), Juice Shop web/REST app
- **§2 Findings** — `Finding #1 - SQL Injection (ZAP plugin 40018)` with
  Severity/Confidence, Affected `GET …/search?q=1`, evidence quoted exactly
  (`Attack: 1' OR '1'='1`), CWE-89, OWASP A03:2021
- **§3 True-Positive Assessment** — header checks = near-certain TPs; SQLi =
  *suspected* (High/Medium) needing manual confirmation; safe read-only
  verification only (dev-tools header inspection)
- **§4 Next Steps** — verify & low-risk fixes, then remediation
- **§5 Confidence & Limitations** — unauthenticated scan, coverage gaps

**1d. Fail-fast on bad data:**
```powershell
python -c "from sentinelai.prompt_engine import build_zap_prompt; build_zap_prompt({'events': [1,2]})"
```
→ `ValueError: Expected ZAP active-scan findings schema JSON (…'alerts' list…)`

### Step 2 — Day 37: the authorization-flow team demo

**2a. The one-command rehearsal (the demo itself):**
```powershell
python tests/demo_authorization_flow.py
```
→
```
=== Day 37 authorization-flow demo rehearsal (gate: 180s) ===
  PASS 0 preflight (10.6s) — SentinelAI, version 1.0.0
  PASS 1 token + .well-known publish + local server (0.0s) — token=9on5s1Gp… http://127.0.0.1:<port>
  PASS 2 GRANT: consent + domain verify + scan (real CLI) (7.6s) — consent typed + domain verified + nmap ran
  PASS 3 DENY: wrong token blocks before scan (real CLI) (6.0s) — blocked with token_mismatch; no scan ran
  PASS 4 GUARD: --active --yes rejected (3.7s) — exit != 0, --yes message present
  PASS 5 audit trail (grant -> verified -> fresh grant -> denied) (0.0s) — 4 records
TOTAL 28.3s / 180s gate — PASSED
```

**2b. Presenter's optional live-typing moment** (show the human step):
```powershell
# terminal 1 — publish + serve a token
python -c "from sentinelai.domain_verify import generate_verify_token, verify_token_publish_line; import pathlib; p=pathlib.Path('demo_site/.well-known'); p.mkdir(parents=True, exist_ok=True); (p/'sentinelai-verify.txt').write_text(verify_token_publish_line(generate_verify_token())+'\n', encoding='utf-8'); print('token published')"
python -m http.server 8000 --directory demo_site
# terminal 2 — type the attestation by hand
python sentinelai.py scan --target http://127.0.0.1:8000 --active --verify-token <TOKEN> --fast
```
→ red panel → type the sentence → `[+] Both authorization checks passed - active testing authorized` → nmap results.

---

## Part 3 — Quick-reference

| Day | Feature | Quick verification | Expected |
|---|---|---|---|
| 36 | ZAP prompt → live LLM | `python tests/test_day36_zap_prompt_llm.py --self-test` | PASSED (offline) |
| 36 | Same, real model | `… --live --provider gemini --force` | `day36_analysis_zap.md` + checks PASSED |
| 37 | Authorization-flow demo | `python tests/demo_authorization_flow.py` | 6/6 PASSED, < 180 s |
| 37 | Deny path | `demo_authorization_flow.py` stage 3 | `token_mismatch`, no scan |
| 37 | `--active --yes` guard | stage 4 | exit ≠ 0 + message |

## Part 4 — Where the full detail lives

`WEEK_5_DAY_36_REPORT.md` · `WEEK_5_DAY_37_REPORT.md` · `day36_analysis_zap.md`
· `day35_sample_zap_findings.json` · `tests/test_day36_zap_prompt_llm.py`
· `tests/demo_authorization_flow.py` · prior: `DAYS_30_35_SUMMARY.md`,
`WEEK_5_DAY_31..35_REPORT.md`, `WEEK_5_SUMMARY.md`
---
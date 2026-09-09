# Days 30–35 — Sprint Summary & Feature-Verification Guide

**Project:** SentinelAI CLI · Team Finatics · CodeQuest 4.0
**Scope:** Day 30 (30-day sprint sign-off) through Day 35 (Feature Sprint: Active Testing & Authorization + ZAP prompt v1)
**Updated:** 2026-09-09 · branch `affan-continued` @ `b79a4b2` (all commits pushed)

This file condenses the per-day reports (`DAY_30_MILESTONE_REPORT.md`,
`WEEK_5_DAY_31_REPORT.md` … `WEEK_5_DAY_35_REPORT.md`) into one page: **what was
built each day**, then a **stepwise verification playbook** — exact commands and
the exact output you should see.

---

## Part 1 — What happened each day

### Day 30 — Milestone review & sign-off (the baseline)
- **Task:** All-features checklist, final team sign-off, milestone report.
- **Result:** 30-day sprint **signed off**: 15/15 feature checklist, 115/115 pytest,
  live one-command E2E 4/4 (≈113 s), demo rehearsal 110.5 s / 180 s gate, `main` clean.
- **Proof:** `DAY_30_MILESTONE_REPORT.md` · commits `1e268af` + `e0adf67` (on `main`).

### Day 31 — Consent-gate attestation flow (design)
- **Task:** *"Design the consent-gate attestation flow — exact wording, CLI prompt structure."*
- **Delivered:** Finalized attestation text + red warning panel wording + UX flow
  (consent → domain verify → scan), audit-record schema, and the rule that active
  testing can never be auto-approved.
- **Files:** `WEEK_5_DAY_31_REPORT.md` (design doc; no product code this day).
- **Commit:** `87bfeb3`.

### Day 32 — `request_consent()` (typed attestation + audit logging)
- **Task:** *"Build request_consent() with typed-phrase matching + audit logging."*
- **Delivered:** `sentinelai/consent.py` — red "ACTIVE TESTING" panel, the exact
  sentence must be typed (3 attempts; case/spacing-insensitive, words exact),
  `quit`/Ctrl+C cancels, **every attempt appended to `consent_audit_log.jsonl`**,
  `assume_yes` hard-blocked.
- **Files:** `sentinelai/consent.py`, `tests/test_consent.py` (12 tests).
- **Commit:** `cc85850`.

### Day 33 — Domain verification (token generator + `.well-known` checker)
- **Task:** *"Build domain verification — token generator + .well-known file checker."*
- **Delivered:** `sentinelai/domain_verify.py` — `generate_verify_token()`,
  `verify_token_publish_line()`, tolerant file parser, URL normalizer, and
  `verify_domain_ownership()` (real HTTPS fetch by default, injectable fetcher for
  offline tests). **Tested against a live test file**: a real local HTTP server —
  which caught a real `urllib` bug (404 raised as `HTTPError`, mis-mapped to
  `unreachable`) that mocks would have missed.
- **Files:** `sentinelai/domain_verify.py`, `tests/test_domain_verify.py` (18),
  `tests/test_domain_verify_live.py` (3 scenarios).
- **Commit:** `93f99ae`.

### Day 34 — `--active` wiring in both CLIs (+ scanner fixes)
- **Task:** *"Wire consent gate + domain verification into the CLI behind an --active flag."*
- **Delivered:** `sentinelai/active_gate.py` (shared two-gate authorization:
  `authorize_active_testing()`, `active_scan_host()`) and `--active` +
  `--verify-token` flags on `scan` in **both** parity-locked CLIs. `--active
  --yes` and `--active --json/--json-file` are rejected up-front; nothing scans
  until both gates pass; the URL target is reduced to a plain host for the nmap
  stage. (Side fix in this session: `scanner.py` hostname `TypeError` + stderr
  logging noise.)
- **Files:** `sentinelai/active_gate.py`, `sentinelai/cli.py`, `commands/scan.py`,
  `sentinelai/domain_verify.py` (one constant), `tests/test_active_gate.py` (11),
  `tests/test_active_gate_live.py` (2, real HTTP).
- **Commit:** `4aa2c6a`.

### Day 35 — ZAP findings prompt template v1
- **Task:** *"Design the LLM prompt template for explaining active-scan (ZAP) findings."*
- **Delivered:** `ZAP_ANALYSIS_PROMPT` v1 in `sentinelai/prompt_engine.py` — a
  **third, distinct** template family (web-app persona; ZAP-native fields
  plugin_id/risk/confidence/param/attack-evidence/CWE; section 3 is a
  **True-Positive Assessment**; OWASP Top 10 tags honored or proposed; only
  ZAP's own evidence strings may be referenced; Days 31–34 authorized framing).
  Plus fail-fast builder `build_zap_prompt()` and the schema contract fixture
  `day35_sample_zap_findings.json` that Day 36's live LLM test will use.
- **Files:** `sentinelai/prompt_engine.py`, `day35_sample_zap_findings.json`,
  `tests/test_zap_prompt.py` (13 tests).
- **Commit:** `b79a4b2`.
---

## Part 2 — Verify it yourself, step by step

Run everything from the repo root in PowerShell. Activate the venv first
(`.\venv\Scripts\Activate.ps1`) so `python` resolves — or use
`.\venv\Scripts\python.exe` everywhere instead.

> Convention below: **`$` = the command**, **`→` = the output you should see**
> (abridged to the lines that matter).

### Step 0 — Sanity (30 seconds)

```powershell
python sentinelai.py --version        # → SentinelAI, version 1.0.0
git log --oneline -7                  # → the seven commits b79a4b2 … 87bfeb3 shown above
```

### Step 1 — Day 32: the consent gate

**1a. Automated (no interaction):**
```powershell
python -m pytest tests/test_consent.py -q
```
→ `12 passed` — covers grant, mistype-retry, `quit`, Ctrl+C abort, hidden
normalization rules, and the audit log.

**1b. What sentence does the gate expect?**
```powershell
python -c "from sentinelai.consent import ATTESTATION_TEMPLATE; print(ATTESTATION_TEMPLATE.format(target='https://juice-shop.local'))"
```
→
```
I authorize active security testing of https://juice-shop.local and confirm that I own this system or have written authorization to test it.
```

**1c. Interactive demo (this types into the real gate):**
```powershell
python -c "from sentinelai.consent import request_consent; r = request_consent('https://juice-shop.local'); print('GRANTED' if r.granted else 'DENIED')"
```
→ you will see:
1. A red panel — `⚠️ ACTIVE TESTING — AUTHORIZATION REQUIRED` — with the target,
   the risks, the two-confirmation explanation, and the sentence to type.
2. The prompt `Type the attestation sentence to confirm, or type 'quit'. (attempt 1/3):`
   - Type something wrong → `[!] Attestation did not match. 2 attempt(s) remaining.`
   - Type `quit` → `[!] Consent denied - active testing cancelled by operator.` and `DENIED`
   - Type/paste the exact sentence → `GRANTED`
3. A new `consent_audit_log.jsonl` appears in the repo root. Open it — one JSON
   line per attempt, e.g.:
```json
{"timestamp": "2026-09-09T…", "event": "consent_attempt", "target": "https://juice-shop.local", "decision": "granted", "reason": "attestation_match", "typed_length": 133, "user": "…", "host": "…", "version": "1.0.0"}
```
(Deleting the file afterwards is safe — it is a local trail, and it will be
recreated on the next attempt. Every run in this guide appends to it.)

### Step 2 — Day 33: domain verification

**2a. Automated (offline, mocked fetch):**
```powershell
python -m pytest tests/test_domain_verify.py -q
```
→ `18 passed`

**2b. Live check — real HTTP server, real fetch, no mocks** (the Day 33 deliverable):
```powershell
python tests/test_domain_verify_live.py
```
→
```
  1_matching_token: {"host": "127.0.0.1:<port>", "verified": true, "reason": "verified", "status_code": 200}
  2_wrong_token: {"verified": false, "reason": "token_mismatch", "status_code": 200}
  3_missing_file: {"verified": false, "reason": "file_not_found", "status_code": 404}
  audit_records: 3
LIVE DOMAIN-VERIFY CHECK PASSED (3/3 scenarios, 3 audit records)
```

**2c. Token generator + the exact line an admin must publish:**
```powershell
python -c "from sentinelai.domain_verify import generate_verify_token, verify_token_publish_line; t = generate_verify_token(); print('TOKEN:', t); print('PUBLISH:', verify_token_publish_line(t))"
```
→
```
TOKEN: 4Kq9…43-char-url-safe-string…
PUBLISH: sentinelai-verify-token: 4Kq9…same-token…
```
### Step 3 — Day 34: the `--active` gate in the real CLI

**3a. Automated:**
```powershell
python -m pytest tests/test_active_gate.py -q        # → 11 passed
python tests/test_active_gate_live.py                # → ALL 2/2 … PASSED (real HTTP)
```

**3b. The guards (safe to try — nothing runs):**
```powershell
python sentinelai.py scan --target https://demo.testfire.net --active --yes
```
→ exit code **1**, and:
```
Error: Active testing cannot be approved with --yes: you must type the attestation sentence verbatim (Day 32 consent gate).
```
```powershell
python sentinelai.py scan --target https://demo.testfire.net --active --json
```
→ exit code **1**, and:
```
Error: Active testing is interactive (consent attestation + domain verification) and cannot be combined with --json / --json-file.
```

**3c. Full gated flow, end to end (local lab, ~1 minute):**

```powershell
# 1) Generate a token and publish it as a real .well-known file
python -c "from sentinelai.domain_verify import generate_verify_token, verify_token_publish_line; import pathlib; t = generate_verify_token(); p = pathlib.Path('demo_site/.well-known'); p.mkdir(parents=True, exist_ok=True); (p / 'sentinelai-verify.txt').write_text(verify_token_publish_line(t) + '\n', encoding='utf-8'); print('TOKEN:', t)"

# 2) Serve it (leave this terminal running; Ctrl+C stops it later)
python -m http.server 8000 --directory demo_site
```
In a **second** terminal:
```powershell
python sentinelai.py scan --target http://127.0.0.1:8000 --active --verify-token <PASTE-TOKEN> --fast
```
→ you will see, in order:
1. The red `⚠️ ACTIVE TESTING — AUTHORIZATION REQUIRED` panel for `http://127.0.0.1:8000`
2. Type the attestation sentence (shown in the panel) →
   `[+] Both authorization checks passed - active testing authorized`
3. `[*] Scan stage target: 127.0.0.1` (URL reduced to a host for nmap)
4. The normal fast nmap run → `[+] Scan completed successfully!` → `SCAN RESULTS` panel

Negative variations (same command, change one thing):
- `--verify-token wrong-token-value` → after consent:
  `[!] Active testing blocked: Domain verification failed: token_mismatch (status=200, url=http://127.0.0.1:8000/.well-known/sentinelai-verify.txt)` — **no scan runs**
- Omit `--verify-token` → hidden prompt: `Paste the verification token published at .well-known/sentinelai-verify.txt:`
- Delete `demo_site/.well-known/sentinelai-verify.txt` → `… Domain verification failed: file_not_found (status=404 …)`

Audit trail check — `consent_audit_log.jsonl` now ends with:
```
{"event": "consent_attempt",  "decision": "granted", "reason": "attestation_match", …}
{"event": "domain_verify",    "decision": "verified", "reason": "verified", "status_code": 200, …}
```

### Step 4 — Day 35: the ZAP findings prompt (template v1)

**4a. Automated:**
```powershell
python -m pytest tests/test_zap_prompt.py -q        # → 13 passed
```

**4b. Build the real prompt from the schema fixture:**
```powershell
python -c "import json; from sentinelai.prompt_engine import build_zap_prompt; d = json.load(open('day35_sample_zap_findings.json', encoding='utf-8')); p = build_zap_prompt(d); print(len(p), 'chars'); print(p.splitlines()[1])"
```
→
```
<N> chars        (several thousand — template + compact JSON payload)
You are a senior web-application security analyst assistant helping a student
```
Sanity checks on the built prompt: it contains all five section headings
(`## 1. Plain-English Summary` … `## 5. Confidence & Limitations`), the fixture's
alerts (`"plugin_id":40018` …), and the authorized-active-test framing.

**4c. Prove it rejects wrong data (fail-fast):**
```powershell
python -c "from sentinelai.prompt_engine import build_zap_prompt; build_zap_prompt({'events': [1, 2]})"
```
→
```
…ValueError: Expected ZAP active-scan findings schema JSON (an object with an 'alerts' list), e.g. from a ZAP JSON export or day35_sample_zap_findings.json. Got: dict.
```

### Step 5 — Full regression (one command, everything)
```powershell
python -m pytest tests/test_zap_prompt.py tests/test_prompt_engine.py tests/test_active_gate.py tests/test_active_gate_live.py tests/test_domain_verify.py tests/test_domain_verify_live.py tests/test_consent.py tests/test_cli_sync.py tests/test_ui.py tests/test_routing.py tests/test_log_parser.py tests/test_event_bridge.py tests/test_mapping.py -q
```
→ `123 passed, 1 warning in ~5s` (the warning is a pre-existing dependency notice).

---

## Part 3 — Quick reference

| Day | Feature | Quick check | Expected |
|---|---|---|---|
| 30 | 30-day sprint sign-off | `DAY_30_MILESTONE_REPORT.md` | 15/15 features, sign-off |
| 31 | Consent design | `WEEK_5_DAY_31_REPORT.md` | wording + UX flow |
| 32 | Consent gate | `pytest tests/test_consent.py -q` | 12 passed |
| 33 | Domain verification | `python tests/test_domain_verify_live.py` | LIVE PASSED 3/3 |
| 34 | `--active` wiring | `pytest tests/test_active_gate.py -q` | 11 passed |
| 34 | CLI guards | `scan … --active --yes` | exit 1 + message |
| 35 | ZAP prompt v1 | `pytest tests/test_zap_prompt.py -q` | 13 passed |
| — | Everything | Step 5 command | 123 passed |

## Part 4 — Notes & troubleshooting

- **Audit trail:** `consent_audit_log.jsonl` is created in the current working
  directory by consent/domain attempts (incl. this guide's demos). It is the
  feature, not a bug — inspect it, and delete it whenever you like.
- **Direct `python -c` consent runs on Windows:** if the Rich panel shows
  escape-garbage under a cp1252 pipe, prefix the command with
  `$env:PYTHONIOENCODING='utf-8'` (the pytest/direct script runners already
  handle this).
- **`--active` is interactive on purpose:** it refuses `--yes` (Day 32 rule) and
  machine modes (Day 24 JSON-purity rule). Passive scans keep the old
  `--confirm`/`--yes` flow.
- **ZAP execution is not in the CLI yet** (Affan's track, Days 36/38–40). Day 35's
  template covers the *findings* half; Day 36 tests it against mock findings.
- **Port already in use** for the demo server? Serve on another port (e.g. `8123`)
  and use `--target http://127.0.0.1:8123`.

## Where the detailed day reports live

`DAY_30_MILESTONE_REPORT.md` · `WEEK_5_DAY_31_REPORT.md` · `WEEK_5_DAY_32_REPORT.md`
· `WEEK_5_DAY_33_REPORT.md` · `WEEK_5_DAY_34_REPORT.md` · `WEEK_5_DAY_35_REPORT.md`
· Day 1–30 command history: `TESTING_GUIDE_DAY1_30.md`; Days 31–35 history: this file.
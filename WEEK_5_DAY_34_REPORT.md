# Week 5 — Day 34 Report (Feature Sprint)

**Date:** 2026-09-08
**Owner:** Aditya Gupta (Project Lead — AI/LLM Integration)
**Plan task (Day 34):** Wire consent + domain verification into the CLI behind the `--active` flag
**Status:** ✅ COMPLETE — 11/11 offline + 2/2 live tests, 110/110 full regression, CLI smoke-tested

---

## 1. What Day 34 delivers

The `--active` flag now exists on `scan` in **both parity-locked CLIs** and blocks
until **both** authorization gates pass, in order:

1. **Consent attestation** (Day 32) — exact typed sentence, audited, `--yes`-proof
2. **Domain verification** (Day 33) — token published at `.well-known/sentinelai-verify.txt`

Any failure is **fail-closed**: nothing scans, and every attempt lands in the shared
`consent_audit_log.jsonl`.

## 2. Files

| File | Change |
|---|---|
| `sentinelai/active_gate.py` | **NEW** — shared gate: `authorize_active_testing()` (consent → token prompt → domain verify), `ActiveAuthorization` result dataclass, `active_scan_host()` (URL → hostname for the nmap stage) |
| `sentinelai/cli.py` | `--active` + `--verify-token` on package CLI; guard + gate wiring in `scan` |
| `commands/scan.py` | Identical `--active` + `--verify-token` wiring on root CLI (parity-locked) |
| `sentinelai/domain_verify.py` | Additive: `REASON_NO_TOKEN_PROVIDED = "no_token_provided"` (no token given → fetch never ran) |
| `tests/test_active_gate.py` | **NEW** — 11 offline tests (gate matrix, audit order, assume-yes block, URL→host, CLI rejections) |
| `tests/test_active_gate_live.py` | **NEW** — 2 live tests: real local HTTP server serving the verify file, REAL urllib fetcher, no mocks |

## 3. Authorization matrix (all fail-closed)

| Scenario | Outcome | Audited |
|---|---|---|
| Attestation typed verbatim + token matches published file | ✅ authorized | `granted` → `verified` |
| Attestation denied / mistyped 3× | ❌ blocked before domain check | `denied` only |
| Attestation granted, token mismatch / 404 / unreachable | ❌ blocked | `granted` → `denied` |
| No token provided (flag or hidden prompt) | ❌ blocked, fetch never runs | `granted` → `denied` (`no_token_provided`) |
| `--active --yes` | ❌ rejected up-front, nothing prompted, nothing audited | none |
| `--active --json` / `--json-file` | ❌ rejected (gate is interactive by design) | none |

## 4. UX flow (interactive)

```
scan --target https://juice-shop.local --active
  ├─ ⚠️ ACTIVE TESTING — AUTHORIZATION REQUIRED   (red panel, exact sentence shown)
  ├─ type sentence verbatim (3 attempts)          → consent_audit_log.jsonl
  ├─ Paste verification token (hidden input)      → or pass --verify-token
  ├─ GET https://juice-shop/.well-known/sentinelai-verify.txt
  ├─ ✓ Both authorization checks passed - active testing authorized
  └─ nmap scan stage runs against the HOST (URL reduced: port stays ZAP's concern)
```

## 5. Validation (all green)

```
py_compile active_gate.py + both test files                          → OK
python tests/test_active_gate.py       (offline, no network)         → 11/11 PASSED
python tests/test_active_gate_live.py  (real HTTP server + urllib)  → 2/2 PASSED
pytest 12 suites (gate offline+live, domain, consent, cli_sync, ui,
       routing, log_parser, event_bridge, prompt_engine, mapping)    → 110 passed
CLI smoke: scan --target ... --active --yes                          → exit 1,
       "Active testing cannot be approved with --yes" (root CLI)
```

Notes:
- Live tests catch what fakes can't (real `urllib` behaviors, header/status handling).
- Test runners force UTF-8 stdout (`reconfigure`) so Rich's Unicode panel survives
  Windows cp1252 pipe captures — direct-run harness fix only, not product code.
- No `consent_audit_log.jsonl` leaked into the repo; all test audits go to temp dirs.

## 6. How to demo (local lab)

```powershell
# 1. Publish a token for your lab host
python -c "from sentinelai.domain_verify import generate_verify_token, verify_token_publish_line; t=generate_verify_token(); print(t); print(verify_token_publish_line(t))"
# 2. Serve the token at  http://<host>/.well-known/sentinelai-verify.txt
# 3. Run the gated scan
python sentinelai.py scan --target http://<host> --active --verify-token <TOKEN>
```

## 7. Scope / next

- No ZAP code here — ZAP execution is Affan's track (Days 36, 38–40).
- Next (Day 35): continue the feature sprint — LLM explanation pipeline for
  active-testing findings (prompt design over scan results), per the 114-day plan.

---

**Commit-ready files:** `sentinelai/active_gate.py`, `sentinelai/cli.py`,
`commands/scan.py`, `sentinelai/domain_verify.py`, `tests/test_active_gate.py`,
`tests/test_active_gate_live.py`

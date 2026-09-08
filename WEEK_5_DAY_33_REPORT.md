# Week 5 — Day 33: Domain Verification — Token Generator + `.well-known` Checker

**Date:** 2026-09-08
**Developer:** Aditya Gupta (Project Lead & LLM)
**Sprint:** SentinelAI 114-Day Plan | Feature Sprint (Days 31–44) — Active Testing & Authorization | Week 5, Day 33
**Day 33 task:** *"Build domain verification — token generator + `.well-known` file checker."*
**Deliverable:** ✅ **`verify_domain_ownership()` function tested against a live test file** (real local HTTP server, 3/3 scenarios, 3 audit records)

---

## 1. What was built

New module **`sentinelai/domain_verify.py`** — the **second layer** of the two-layer
authorization system designed on Day 31. After the consent gate (`consent.py`, Day 32)
passes, active testing must also prove the target's *real administrator* consents by
publishing a token file that `verify_domain_ownership()` fetches and compares.

| API | Purpose |
|---|---|
| `generate_verify_token(nbytes=32)` | Cryptographically random URL-safe token (`secrets.token_urlsafe`) |
| `verify_token_publish_line(token)` | The exact line an admin places in the file: `sentinelai-verify-token: <tok>` |
| `extract_verify_token(content)` | Tolerant parser: canonical line (case/space-insensitive) or bare single-token file |
| `verification_url(host, scheme="https")` | Normalizes any host string (`juice-shop.local`, `https://host/path`, `host:port`) to `https://<host>/.well-known/sentinelai-verify.txt` |
| `verify_domain_ownership(host, token, *, scheme, timeout, fetch, audit_path)` | **The deliverable** — fetches the file, compares tokens, audits every outcome |
| `DomainVerificationResult(verified, host, reason, timestamp, status_code, url)` | Dataclass outcome for Day 34 CLI wiring |
| `DomainVerificationError(ValueError)` | Mirror of `ConsentError`/`ApprovalError` for one shared error surface |

### Decision matrix (`verify_domain_ownership`)
| Published file | Result | Audit decision · reason |
|---|---|---|
| Token matches exactly | ✅ verified | `verified · verified` |
| Wrong token | ❌ denied | `denied · token_mismatch` |
| File missing (HTTP 404) | ❌ denied | `denied · file_not_found` |
| File present but no usable token | ❌ denied | `denied · no_token_found` |
| Host unreachable / timeout | ❌ denied | `denied · unreachable` |

**Design rules (fail-closed):** no `assume_yes` path → a network/transport failure is
always **denied**; every outcome (grant **and** deny) appends one JSONL line to
`consent_audit_log.jsonl` (`event: "domain_verify"`, with `url`, `status_code`,
`user`, `host`, `version`) — the same trail as the consent gate. The fetcher is
injectable (`fetch: callable -> (status_code, body)`) so offline tests never touch the
network; default uses the stdlib (`urllib`) — no new dependency.

## 2. Real bug caught by the "live test file" deliverable

While proving the function against a **real local HTTP server** (not a mock), the live
check failed: a genuinely-missing file returned `unreachable` instead of `file_not_found`.

**Root cause:** `urllib.request.urlopen()` **raises `HTTPError`** on 4xx/5xx responses —
it does *not* return a response object. `_default_fetch` only handled the success path,
so a real 404 propagated as an exception and was mis-mapped to `unreachable`. (The
offline fake-fetch tests used `(404, ...)` tuples and couldn't catch this.)

**Fix:** `_default_fetch` now catches `HTTPError` → `(exc.code, "")`, and lets only
connection-level `URLError`s propagate. This is exactly why the plan demanded a
*a live test file* — a pure-mock suite would never have caught it.

## 3. Files changed

| File | Change |
|---|---|
| `sentinelai/domain_verify.py` | **New** — domain verification module (Day 33 task) |
| `tests/test_domain_verify.py` | **New** — 18 offline tests (token gen, publish line, parser, URL normalization, full decision matrix, audit, input validation) |
| `tests/test_domain_verify_live.py` | **New** — **live** check: real `ThreadingHTTPServer` on 127.0.0.1 serving `.well-known/sentinelai-verify.txt`; 3 scenarios + audit assertions |

No changes to existing modules — additive, ready for Day 34 `--active` wiring.

---

## 4. Validation

### Offline suite
```
$ python -m py_compile sentinelai/domain_verify.py tests/test_domain_verify.py tests/test_domain_verify_live.py   # COMPILE OK
$ python -m pytest tests/test_domain_verify.py -q          # 18 passed
```

### LIVE check against a real test file (the Day 33 deliverable)
Runs `verify_domain_ownership()` with its real urllib fetch against a local
`ThreadingHTTPServer` serving `.well-known/sentinelai-verify.txt`:
```
$ python tests/test_domain_verify_live.py
  1_matching_token: {"verified": true,  "reason": "verified",       "status_code": 200}
  2_wrong_token:    {"verified": false, "reason": "token_mismatch", "status_code": 200}
  3_missing_file:   {"verified": false, "reason": "file_not_found", "status_code": 404}
  audit_records: 3
LIVE DOMAIN-VERIFY CHECK PASSED (3/3 scenarios, 3 audit records)
```
Audit trail: `[verified, denied, denied]` — exactly as designed.

### Full regression
`97 passed` across domain_verify (offline + live), consent, cli_sync, ui, routing,
log_parser, event_bridge, prompt_engine, mapping (0 failures).

## 5. Day 34 preview (Aditya track)

- Wire **both** authorization layers behind `scan --active` on both CLI entry points
  (parity-locked via `tests/test_cli_sync.py`): consent gate → domain verification →
  only then hand off to Affan's ZAP active-scan box. `--active` blocks until both
  checks pass; `--active --yes` stays rejected.
- CLI gains token management (`generate-verify-token` snippet / instructions printout).

## Sign-Off

**Day 33 Status:** ✅ **COMPLETE** — `verify_domain_ownership()` built (token generator +
`.well-known` checker + fail-closed audit trail) and **tested against a live test file**
(real local HTTP server; the live test caught a real urllib-HTTPError bug that mocks
would miss). Validated: 18 offline tests + live 3/3 + full regression 97 passed.

**Developer:** Aditya Gupta | **Team:** Team Finatics | **CodeQuest 4.0**
# Week 5 — Day 32: `request_consent()` — Typed-Phrase Matching + Audit Logging

**Date:** 2026-09-07
**Developer:** Aditya Gupta (Project Lead & LLM)
**Sprint:** SentinelAI 114-Day Plan | Feature Sprint (Days 31–44) — Active Testing & Authorization | Week 5, Day 32
**Day 32 task:** *"Build `request_consent()` function with typed-phrase matching + audit logging → `consent_audit_log.jsonl` recording every attempt (granted or denied)."*
**Deliverable:** ✅ `sentinelai/consent.py` + `tests/test_consent.py` (12/12 offline tests pass)

---

## 1. What was built

New module **`sentinelai/consent.py`** implementing the consent-gate front half of the
two-layer authorization system designed on Day 31:

| API | Purpose |
|---|---|
| `request_consent(target, *, audit_path, prompt, max_attempts, assume_yes)` | Interactive typed-attestation gate; returns `ConsentResult` (granted/denied + reason) |
| `expected_attestation(target)` | Builds the exact normalized sentence the operator must type |
| `ConsentError(ValueError)` | Mirror of `ApprovalError` for a shared error surface in the CLI |
| `ConsentResult(granted, reason, target, timestamp, typed, attempts)` | Dataclass outcome for the CLI (Day 34 wiring) |
| `ATTESTATION_TEMPLATE` | The exact sentence (quotes optional when typed) |

### Flow

1. Render the red **"ACTIVE TESTING — AUTHORIZATION REQUIRED"** panel (reuses `ui.print_panel`)
   stating target, ZAP engine, risks, the two confirmation layers, and the exact phrase.
2. Loop up to `max_attempts` (default 3):
   - **cancel words** (`quit`/`abort`/`no`/…) → denied (`user_cancel`)
   - **normalized match**  → granted (`attestation_match`)
   - **otherwise** → denied (`attestation_mismatch`) + warn, retry
3. `Ctrl+C` / EOF (`KeyboardInterrupt`, `click.Abort`) → denied (`aborted`) — **never** lets the scan run.
4. Every attempt appends one JSONL line to `consent_audit_log.jsonl` (written **before** a grant returns — fail-closed), including user/host/version for accountability.

## 2. Matching semantics (from the Day 31 design)

- Normalization is minimal: strips one pair of outer quotes (with or without quotes both pass),
  collapses whitespace, lowercases, trims.
- **Words must be exact** — a typo is a mismatch; case/spacing variance passes.
- No `--yes` / `assume_yes` bypass: passing `assume_yes=True` raises `ConsentError`
  ("Active testing cannot be approved with --yes / assume_yes…") so no caller can auto-approve active testing.

## 3. Audit schema (one JSON line per attempt)

```json
{"timestamp": "...", "event": "consent_attempt", "target": "…", "decision": "granted"|"denied",
 "reason": "attestation_match"|"attestation_mismatch"|"user_cancel"|"aborted",
 "typed_length": 102, "user": "…", "host": "…", "version": "1.0.0"}
```
Append-only, `utf-8`, local-only. I/O failure to write the log raises `ConsentError`
(fail-closed) rather than silently proceeding.

## 4. Files changed

| File | Change |
|---|---|
| `sentinelai/consent.py` | New — consent gate module (Day 32 task) |
| `tests/test_consent.py` | New — 12 offline tests (exact match, quotes/case/spacing, mismatch every-attempt log, retry-then-grant, quit, Ctrl+C abort, blank input, empty target, assume_yes rejected, audit optional, normalize, expected_attestation) |

No changes to existing modules — the module is additive and not yet wired into the CLI
(CLI `--active` wiring is Day 34, per plan).

## 5. Validation

```
$ python -m py_compile sentinelai/consent.py tests/test_consent.py      # COMPILE OK
$ python -m pytest tests/test_consent.py -q                             # 12 passed in 0.84s
$ python tests/test_consent.py                                          # ALL 12/12 PASSED (offline, direct-run)
```

The direct-run path also demonstrates the Rich panel (`⚠️ ACTIVE TESTING — AUTHORIZATION REQUIRED`)
renders correctly, mismatch retries warn ("Attestation did not match. N attempt(s) remaining."),
and all audit writes go to caller-provided paths (test temp dirs) — no `consent_audit_log.jsonl`
is created in the repo by tests.

Sneha's Day 31 consent-gate tests (exact match / mismatch / empty input) overlap with the
first three tests here; when her suite lands, both can merge under `tests/test_consent.py`.

## 6. Day 33 preview (Aditya track)

- `verify_domain_ownership(target)` — token generator + `.well-known/sentinelai-verify.txt`
  checker (mocked-HTTP tests per Sneha's Day 32 track).
- Then Day 34 wires `request_consent()` + `verify_domain_ownership()` behind `--active` in
  both CLI entry points (parity-locked via `test_cli_sync.py`).

## Sign-Off

**Day 32 Status:** ✅ **COMPLETE** — `request_consent()` built with typed-phrase matching,
3-attempt denial, cancel/abort handling, fail-closed `consent_audit_log.jsonl` audit trail,
and `assume_yes` hard-block; validated offline (12/12).

**Developer:** Aditya Gupta | **Team:** Team Finatics | **CodeQuest 4.0**
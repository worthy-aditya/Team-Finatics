# Week 5 — Day 37 Report (Feature Sprint)

**Date:** 2026-09-10
**Owner:** Aditya Gupta (Project Lead — AI/LLM Integration)
**Branch:** `aditya-dev`
**Plan task (Day 37):** Team sync — demo consent gate + domain verification end-to-end
**Status:** ✅ COMPLETE — automated live demo rehearsal **PASSED 6/6 stages, 28.3 s / 180 s gate** (zero mocks, real CLI, real HTTP, real nmap)

---

## 1. Deliverable

The plan's deliverable is *"Full authorization flow demoed live to team."*
Delivered as a **timed, automated demo rehearsal** — `tests/demo_authorization_flow.py`
(Day 27 `demo_rehearsal.py` conventions) — that anyone can run before or during the
team sync to prove the whole Days 31–34 chain works live, end to end, with **zero mocks**:

```powershell
python tests/demo_authorization_flow.py            # full timed rehearsal
python tests/demo_authorization_flow.py --keep     # + keep artifacts
```

## 2. The 6 demo stages (what the team sees)

| # | Stage | Proves |
|---|---|---|
| 0 | preflight | nmap on PATH; CLI starts (`SentinelAI, version 1.0.0`) |
| 1 | token + `.well-known` publish + local server | an admin can publish the Day 33 verify file in seconds |
| 2 | **GRANT** (real CLI subprocess) | red attestation panel shown → operator types the exact sentence → `Both authorization checks passed` → `.well-known` token verified over **real HTTP** → nmap fast scan runs → results panel |
| 3 | **DENY** (real CLI) | fresh attestation granted, then **wrong token → `token_mismatch` block, no scan runs** |
| 4 | **GUARD** | `--active --yes` rejected up-front (exit ≠ 0, Day 32 message) |
| 5 | audit trail | `consent_audit_log.jsonl` captured **4 records**: `consent_attempt:granted → domain_verify:verified → consent_attempt:granted → domain_verify:denied` |

Recorded run (this repo, today):

```
=== Day 37 authorization-flow demo rehearsal (gate: 180s) ===
  PASS 0 preflight (10.6s) — SentinelAI, version 1.0.0
  PASS 1 token + .well-known publish + local server (0.0s) — token=9on5s1Gp… http://127.0.0.1:12060
  PASS 2 GRANT: consent + domain verify + scan (real CLI) (7.6s) — consent typed + domain verified + nmap ran
  PASS 3 DENY: wrong token blocks before scan (real CLI) (6.0s) — blocked with token_mismatch; no scan ran
  PASS 4 GUARD: --active --yes rejected (3.7s) — exit != 0, --yes message present
  PASS 5 audit trail (grant -> verified -> fresh grant -> denied) (0.0s) — 4 records
TOTAL 28.3s / 180s gate — PASSED
```

## 3. What the rehearsal itself taught (a real catch)

The first run FAILED stage 5 — my assertion expected 3 audit records
(`granted → verified → denied`), but the trail correctly held **4**:
`granted → verified → granted → denied`. Every active-scan attempt **re-attests by
design** (no session reuse), so the deny run legitimately produces a fresh consent
grant before the token mismatch. Exactly what a rehearsal is for: the demo record
now documents that behavior for the team.

## 4. How to run the team-sync demo (presenter walkthrough)

1. `python tests/demo_authorization_flow.py` — the 6-stage record above is the demo.
2. Optional live-typing moment: run
   `python sentinelai.py scan --target http://127.0.0.1:<port> --active` against a
   published token file and type the attestation by hand (steps in
   `WEEK_6_SUMMARY.md` Part 2, Step 3c).
3. Talking points: two-layer authorization (Day 32 consent + Day 33 domain
   verification), fail-closed design, unified audit trail, `--yes`/JSON guards.

## 5. Validation

```
py_compile tests/demo_authorization_flow.py                            → OK
python tests/demo_authorization_flow.py                                → 6/6 PASSED, 28.3s / 180s gate
pytest regression suites (day36, zap_prompt, prompt_engine, active_gate
       offline+live, domain_verify offline+live, consent, cli_sync, …)  → 124 passed (Day 36 run)
```

Rehearsal runs in a temp dir — nothing leaks into the repo (`--keep` optionally
copies artifacts to `demo_day37_artifacts/`).

## 6. Scope / next

Day 37 closes Aditya's Week-5/6 block (31–37). Next per plan (Days 38–44):
LLM refinements against **real** ZAP output (once Affan's ZAP track lands),
risk-weighting, edge cases (Days 42), positioning doc (43), full demo narrative (44).

---

**Commit-ready files:** `tests/demo_authorization_flow.py`

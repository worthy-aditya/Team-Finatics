# Week 4 — Day 28 Report (Aditya)
**Sprint task:** *"Fix any last issues found in demo rehearsal → All demo blockers resolved."*

**Status:** ✅ **COMPLETE — one real demo blocker surfaced and fixed (transient Gemini rate-limiting), full sweep clean, final rehearsal gate PASSED at 110.5 s / 180 s with zero crashes.**

---

## 1. The blocker Day 28 caught (and the fix)

**First rehearsal run of the day: step 4/5 `analyze scan [gemini]` FAILED (rc=1) after 138 s** — the google-genai SDK looped through its retry budget (`AFC ... max remote calls: 10` lines) and gave up → total 225 s, gate red. Day 27's identical step had passed in 38 s.

**Diagnosis:** standalone reproduction **succeeded minutes later** with a full 5-section analysis → not a code regression but **transient Gemini free-tier rate limiting** (429/quota) after a heavy day of testing. 429 is already in `RETRYABLE_STATUS` with backoff, so sustained quota exhaustion simply outlasts all retries — correct behavior, but a presenter would have been stuck.

**Fixes (defense in depth):**
1. **`sentinelai/prompt_engine.py`** — both Gemini final-error paths now detect the 429/`RESOURCE_EXHAUSTED`/quota pattern (`_gemini_rate_limit_hint()`) and append: *"Wait ~60s and retry, or switch providers with --llm ollama."*
2. **`DEMO_SCRIPT.md`** — new primary fallback row: *"Gemini rate-limits (429) mid-demo → narrate over the committed analysis artifact (`day9_nmap_llm_analysis.md`), zero time cost; or wait ~60 s and rerun."* The scripted recovery costs ~0 s instead of ~95 s.

**Verification of the fix — final gate run:**

```
=== SentinelAI demo rehearsal | cli=root target=127.0.0.1 llm=ollama scan-llm=gemini limit=180s ===
  PASS    0.0s  1/5 SCAN (fixture)            committed fixture reused
  PASS     3.1s  2/5 logs --sample --json     events=3
  PASS    77.7s  3/5 logs --sample --analyze  7481 chars of analysis
  PASS    26.7s  4/5 analyze scan [gemini]    5/5 sections, 7298 chars
  PASS     3.0s  5/5 report                   text report valid

  TOTAL  110.5s of 180s budget (UNDER 3 MINUTES)
  REHEARSAL PASSED
```

## 2. "Last issues" sweep (demo-readiness audit)

| Check | Result |
|---|---|
| Raw `print()` audit (all `sentinelai/*.py`, `commands/*.py`) | ✅ **No prints in any demo path.** Only executable prints are real-log **error handlers** in Affan's `event_logs.py` (admin mode, never hit via `--sample`) + its `__main__` research block; line 440 is inside a docstring |
| Scratch files | ✅ removed empty `_fix_cli21c.py`; no `tempCodeRunnerFile.py` |
| `.env` hygiene | ✅ `.env` exists locally and is confirmed git-ignored; `.env.example` is what's committed |
| Stray artifacts | ✅ none (rehearsal/E2E use self-cleaning temp dirs) |
| Known deferred (not demo blockers) | `natural_cli.py` still on colorama; `event_logs.py` error prints could route through `ui` — both queued as Day 29 "clean code" candidates (Affan's files — to be raised with him, not rewritten unilaterally) |

## 3. Full regression evidence (all green on Day 28)

| Suite | Result |
|---|---|
| ui / event_bridge / routing / log_parser / cli_sync | 6/5/5/8/6 ALL PASSED |
| prompt_engine (after hint change) | ALL PASSED |
| E2E pipeline `--cli both --skip-llm` | PASSED root 15.4 s + pkg 14.5 s |
| Rehearsal gate (live, fixture) | **PASSED 110.5 s / 180 s, 5/5 steps** |
| Gemini standalone repro | PASSED (full 5-section analysis) |

**All demo blockers resolved: ✅** — gate green with the scripted fallback for the one remaining variable (cloud quota) that no code can fully eliminate.

**Next (Day 29):** final PRs to `main` — clean code, no debug prints, review approval; merge plan for `affan-continued` (and reconciling Affan's `fa2e9ae`) is the team-coordination piece.

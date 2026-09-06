# Week 4 — Day 27 Report (Aditya)
**Sprint task:** *"Rehearse demo — run scan + logs commands in live demo flow → Demo runs under 3 minutes with zero crashes; demo commands memorized and running smoothly."*

**Status:** ✅ **COMPLETE — timed rehearsal tool built, one real demo blocker found and fixed, final flow PASSED at 104.5 s / 180 s with zero crashes (5/5 steps).**

---

## What was delivered

### 1. `tests/demo_rehearsal.py` — the repeatable rehearsal gate
Executes the **exact** demo flow end-to-end and enforces the sprint gate programmatically:
- **Preflight (untimed blockers):** Ollama reachable + models present, `GEMINI_API_KEY` check (with graceful fallback notice), nmap on PATH, CLI starts (`--help`)
- **Five timed steps** mirroring `DEMO_SCRIPT.md`: fast scan (`--json-file`) → `logs --sample --json` (JSON-purity check) → `logs --sample --analyze` (analysis length) → `analyze --kind scan` (5-section markdown contract) → `report --format text` (banner check)
- **Gate:** total ≤ 180 s and every step rc=0, else exit 1 with the timing table
- Reuses the Day 25 E2E helpers (`_run`/`DRIVERS`/section contract) — no parallel logic; options: `--target`, `--llm`, `--scan-llm`, `--use-fixture`, `--skip-llm`, `--keep`, `--max-seconds`; not pytest-collected (live/slow by design)

### 2. `DEMO_SCRIPT.md` — the presentation script
T-minus-10 checklist (warm the Ollama model — cold start can eat 30–60 s; venv; nmap; font/notifications; fallback fixture), the five-step flow with time budgets and word-for-word talking points, the **MITRE ATT&CK Q&A table** (4624→T1078 Valid Accounts, 4625→T1110 Brute Force, 4720→T1136 Create Account, 4726→T1531), and a failure→fallback table (Ollama down, Nmap blocked, no key).

### 3. 🐛 Real demo blocker found by the rehearsal — and fixed same day

**Run 1 (both LLM legs on local Ollama): every step passed, but TOTAL = 226.8 s — OVER the 180 s gate.** The two local-model generations alone took 210.7 s (115.7 s + 95.0 s on the 8B `gemma4` model). A unit-test-free, crash-free demo would still have blown the hackathon time slot.

**Fix (demonstrates more, costs less):** route the private event-log leg through **local Ollama** and the shareable scan-report leg through **cloud Gemini** — exactly the Week 3 `--routing` story (`private` → local, `report` → cloud).

**Run 2 (final flow):**

```
=== SentinelAI demo rehearsal | cli=root target=127.0.0.1 llm=ollama scan-llm=gemini limit=180s ===
  PASS     2.8s  1/5 SCAN (--fast)            hosts=1
  PASS     2.3s  2/5 logs --sample --json     events=3
  PASS    58.7s  3/5 logs --sample --analyze  8469 chars of analysis
  PASS    38.3s  4/5 analyze scan [gemini]    5/5 sections, 6952 chars
  PASS     2.4s  5/5 report                   text report valid

  TOTAL  104.5s of 180s budget (UNDER 3 MINUTES)
  REHEARSAL PASSED
```

**104.5 s / 180 s — 42% headroom, zero crashes**, and the narration now includes the routing/privacy story as a feature, not an apology.

Also fixed while building: rehearsal preflight originally probed `version` (pkg-CLI-only) — switched to `--help` (valid on both entry points).

## Reused (nothing rebuilt)
Day 25 E2E subprocess helpers + artifact contracts · Day 21 routing (`--llm` switcher) · Day 24 spinner/Rich output (the spinner is part of the show) · Day 22 event bridge (`--sample`) · Day 10 5-section contract as the pass criterion.

## Notes for Day 28
- Run 1 vs Run 2 shows local-model latency variance (115.7 s → 58.7 s warm) — keep the model warmed right before presenting (checklist step).
- `--scan-llm ollama` remains available for an offline venue, with the documented expectation that it may exceed the gate.
- `demo_artifacts/` from `--keep` runs is scratch output — not committed.

**Next (Day 28):** fix any last issues found in rehearsal → all demo blockers resolved (none currently open; gate green).

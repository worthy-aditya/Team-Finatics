# Week 4 — Day 25 Report (Aditya)
**Sprint task:** *"Write complete end-to-end test — full scan + logs + AI + report in one command → One-command pipeline test passing cleanly."*

**Status:** ✅ **COMPLETE — 4/4 stages PASS on the root CLI (live nmap + live ollama), 3/3 runnable stages PASS on the package CLI; one real cross-week bug found & fixed.**

---

## What was built

### `tests/test_e2e_pipeline.py` — the one-command pipeline test
A **black-box orchestrator**: it does not import internals — it drives the real CLI
through `subprocess` (so any wiring regression between commands fails loudly) and
validates each stage's artifact. One command runs everything:

```
python tests/test_e2e_pipeline.py                       # root CLI, live nmap + ollama
python tests/test_e2e_pipeline.py --cli both            # validate BOTH entry points
python tests/test_e2e_pipeline.py --skip-llm            # stages 1/2/4 only (fast)
python tests/test_e2e_pipeline.py --llm gemini          # cloud leg
pytest tests/test_e2e_pipeline.py                       # opt-in via SENTINELAI_RUN_E2E=1
```

**Stages and pass criteria:**

| Stage | Command exercised | Pass criteria |
|---|---|---|
| 1/4 SCAN | `scan --target 127.0.0.1 --json-file` | rc=0, schema JSON with ≥1 host, ≥0 ports; nmap installed & host reachable (clear skips otherwise) |
| 2/4 LOGS | `logs --sample --json` | rc=0; stdout parses as **pure JSON** (Day 24 purity contract), `events` non-empty |
| 3/4 AI | `analyze -i scan.json --kind scan --llm ollama` | rc=0; Markdown contains **all 5 scan section headers** (Day 10 contract) and ≥500 chars |
| 4/4 REPORT | `report -i scan.json --format json` + `text` | rc=0; JSON report has `details`+`scan_summary`; text has the report banner |

Supports `--cli root|pkg|both` (both entry points), `--target`, `--llm gemini|ollama`,
`--skip-llm`, and a `test_e2e_pipeline()` pytest wrapper (opt-in via env var so the
default offline suite stays fast).

## 🐛 Bug the E2E caught on its very first run (Day 25's real payoff)

**`report` crashed with `KeyError: 'ip'` on every scan produced since Week 2.**
`commands/report.py` only understood the Week-1 schema (`host.ip`, `host.protocols`)
while today's `NmapScanner.parse_results()` emits `host.address`, `host.ports[]`
with nested `service{name,product,version}` — schema drift between Week 1 and
Week 2 that unit tests never crossed because report had no test of its own.

**Fix (schema-tolerant, no parallel code):** added `_normalize_scan()` to
`commands/report.py`, which yields `(ip, status, rows)` from **both** generations;
all three formatters (text/json/csv) now render from the normalized rows. Verified
against both committed fixture generations:
- `scan_results.json` (Week-1 shape) → report OK
- `scan_results_day10_localhost.json` (current shape) → report OK (json/text/csv)

## Validation

- **One-command run (root CLI, live):** `E2E PIPELINE PASSED (4/4 stages) in 110.2s`
  — SCAN hosts=1 open_ports=2 · LOGS events=3 threat=LOW · AI llm=ollama 5/5
  sections (7072 chars) · REPORT json+text valid.
- **Package CLI:** `E2E PIPELINE PASSED (4/4 stages) in 15.6s` (`--skip-llm`).
- **Offline suites re-run after the report fix:** ui 6/6, event_bridge 5/5,
  routing 5/5, log_parser 8/8, cli_sync 6/6, prompt_engine — all PASS.

## Reused (nothing rebuilt)
`sentinelai.py` / `sentinelai/cli.py` commands as-is · `analyze_scan_file()` unified
entry · `logs --sample` (event_bridge) · `report` command · Day 10 section-header
contract as pass criteria · Day 24 JSON-purity contract as stage-2 criteria.

## Notes / follow-ups
- `natural_cli.py` still on colorama (carried from Day 24) — candidate issue.
- Stage 3 defaults to `ollama` (free/local); `--llm gemini` needs `GOOGLE_API_KEY`.
- E2E is **live and slow (~2 min)** by design; it stays opt-out of CI-style offline runs.

**Next (Day 26):** README + architecture diagram + usage documentation.

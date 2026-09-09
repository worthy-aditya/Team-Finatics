# SentinelAI CLI — Hands-On Testing Guide (Days 1–30 Features)

**Audience:** Aditya Gupta (and any teammate) who wants to actually *run* the CLI
and see every feature built across the 30-day sprint working live.

**Project:** Team Finatics · CodeQuest 4.0 · SentinelAI CLI v1.0.0
**Updated:** 2026-09-07 (verified against code on `affan-continued`)

---

## 0. Before you start (30 seconds of setup)

Everything runs from the repo root: `c:\Users\ADITYA GUPTA\Team-Finatics`.

| # | Step | Command (PowerShell) |
|---|------|----------------------|
| 1 | Make sure the virtualenv exists | `Test-Path .\venv\Scripts\python.exe` → should print `True` |
| 2 | Activate it (optional but handy — lets you type `python` instead of the full path) | `.\venv\Scripts\Activate.ps1` |
| 3 | Verify Nmap is installed (needed for live scans) | `nmap --version` (expect `Nmap version …`) |
| 4 | Check LLM options | `ollama --version` (local AI) and/or a `GEMINI_API_KEY` in `.\env` (cloud AI) |

> **No Nmap?** You can still try most of this guide — Days 1–7 output is already
> saved in `scan_results.json` / `scan_results_day10_*.json`, and the event-log
> pipeline has a built-in `--sample` corpus that needs no admin rights at all.
>
> **No Ollama / no Gemini key?** The analysis commands (`--llm` set) will fail cleanly
> with a friendly message; everything else still works. Gemini setup:
> `copy .env.example .env` then paste your key from aistudio.google.com/apikey.
> Ollama setup: install, then `ollama pull llama3`.

### Two ways to run the same CLI (both are verified, pick either)

```powershell
.\venv\Scripts\python.exe sentinelai.py <command>     # root CLI (all commands)
.\venv\Scripts\python.exe -m sentinelai.cli <command> # package CLI (parity-locked)
```

Both expose the **same commands and options** — they're locked together by
`tests/test_cli_sync.py` (Day 25). This guide uses the root entry point
(`sentinelai.py`), and notes the one extra parse-only command available on the
package CLI. If the venv is activated you can write `python sentinelai.py …`
instead.

> Tip: you can verify the two entry points match at any time with:
> `.\venv\Scripts\python.exe -m pytest tests/test_cli_sync.py -q`

---

## 1. Command quick-reference (everything you can run)

| Command | What it does | Built in |
|---|---|---|
| `sentinelai.py --help` | See all commands | Day 3 |
| `sentinelai.py --version` | Show version | Day 3 |
| `sentinelai.py network` | Show local network/OS info | Day 8 |
| `sentinelai.py scan --target <IP>` | Nmap scan (fast / standard / aggressive) → panel + JSON | Days 2–7, 24 |
| `sentinelai.py analyze -i <file> --kind scan\|events --llm gemini\|ollama …` | LLM plain-English analysis (5-section report) | Days 9–14 |
| `sentinelai.py logs [--sample] [--analyze] [--json]` | Windows Event Log read + analyze (demo-safe with `--sample`) | Days 15–19, 22 |
| `python -m sentinelai.cli parse -i <csv\|evtx> --logs` | Raw CSV/EVTX export → analysis-ready JSON | Day 19 |
| `sentinelai.py report -i <scan.json> -f text\|json\|csv` | Generate report artifacts | Days 10, 22–30 |
| `sentinelai.py natural-cli` | Interactive plain-English mode (`scan localhost quickly`, `help`, `exit`) | Day 14 |

**Key options to remember:**
- `scan`: `--fast` / `--aggressive` / `--json` (pure JSON to stdout) / `--json-file`
  (save) / `--confirm` + `--yes` (human-in-the-loop approval, Day 21)
- `analyze`: `--kind scan|events` · `--llm gemini|ollama` · `--routing report|private`
  (Day 21) · `--mode standard|beginner|remediation` (Days 10–17) · `--model` ·
  `--no-save` (don't write an `.md`)
- `logs`: `--sample` (no admin) · `--hours N` · `--event-ids 4624 4625 …` ·
  `-o events.json` · `--analyze` · `--json`
- `report`: `-i <scan json>` · `-o <basename>` · `-f text|json|csv`

Original files for reference: `README.md` (quickstart), `USAGE.md`,
`NATURAL_CLI_GUIDE.md`, and the `WEEK_*_*.md` per-day reports.
---

## 2. Step-by-step: where to start & how the flow goes

The sprint's story is **Scan → Logs → AI → Report**, and the best way to see the
CLI is to walk that same pipeline piece by piece, then run the one-command E2E that
joins it all. Follow the phases in order — each one matches a week of the sprint.

### Phase 0 — Sanity check (2 min, no network)

```powershell
.\venv\Scripts\python.exe sentinelai.py --help        # list every command
.\venv\Scripts\python.exe sentinelai.py --version     # "SentinelAI, version 1.0.0"
.\venv\Scripts\python.exe sentinelai.py network       # hostname, local IP, OS
```

> **What you should see:** a nice set of key–value lines (Hostname, Local IP, OS,
> Python). This proves the venv, Click, and the Rich UI (`sentinelai/ui.py`, Day 24)
> all work.

---

### Phase 1 — Nmap scanning (Days 2–7): make the scanner talk

Start on **your own machine** — fastest, safest, and the exact target the team
validated all week.

```powershell
# 1a. Fast scan (top 20 ports, ~30s)
.\venv\Scripts\python.exe sentinelai.py scan --target 127.0.0.1 --fast

# 1b. Standard scan with service detection, saved to JSON (the "real" flow)
.\venv\Scripts\python.exe sentinelai.py scan --target 127.0.0.1 --json-file scan_results.json

# 1c. Machine mode - pure JSON to stdout, nothing else (pipe-friendly)
.\venv\Scripts\python.exe sentinelai.py scan --target 127.0.0.1 --json
```

**What you should see:**
- A spinner while nmap runs (Day 24), then a **SCAN RESULTS panel** with
  `Host / TCP: open count` and each open port + service (e.g. `135/tcp msrpc`).
- `1b` writes `scan_results.json` (open it if you like).
- `1c` prints *only* JSON (used by the E2E test later).

**Optional — human-in-the-loop approval (Day 21–30 safety):**
```powershell
.\venv\Scripts\python.exe sentinelai.py scan --target scanme.nmap.org --confirm
# answer y/n - if No, the scan is cancelled. Combine with --yes to auto-approve.
```

> **Day 9 edge cases you can demo here:** scan an **offline** IP
> (`--target 192.0.2.1 --fast`) and a **closed** port set. Watch the clean error
> messages instead of a crash (Day 12).
---

### Phase 2 — LLM analysis of a scan (Days 9–14): plain-English findings

Now feed that structured scan JSON to the AI. Same command works for Gemini
(cloud) and Ollama (local).

```powershell
# Pick ONE provider (keep the other for comparison - see Phase 5)
.\venv\Scripts\python.exe sentinelai.py analyze -i scan_results.json --kind scan --llm ollama
.\venv\Scripts\python.exe sentinelai.py analyze -i scan_results.json --kind scan --llm gemini
```

**Add modes & routing (built Days 10–17, 21):**
```powershell
# beginner mode - plain-English teaching tone
.\venv\Scripts\python.exe sentinelai.py analyze -i scan_results.json --llm ollama --mode beginner

# remediation plan - prioritized fix-it steps
.\venv\Scripts\python.exe sentinelai.py analyze -i scan_results.json --llm ollama --mode remediation

# routing: report -> gemini (cloud), private -> ollama (local); explicit --llm always wins
.\venv\Scripts\python.exe sentinelai.py analyze -i scan_results.json --routing private
.\venv\Scripts\python.exe sentinelai.py analyze -i scan_results.json --routing report

# don't save a file, just print it
.\venv\Scripts\python.exe sentinelai.py analyze -i scan_results.json --llm ollama --no-save
```

**What you should see:** a strict 5-section Markdown report rendered in the
terminal (Day 24): **1 Summary · 2 Ranked risk findings · 3 What this suggests ·
4 Next steps · 5 Confidence & limitations** — and the same text auto-saved as
`*.md` (default `day9_nmap_llm_analysis.md`). The provider + model are printed at
the end (e.g. `[+] LLM analysis generated via ollama with llama3`).

> Pre-built sample outputs you can compare against:
> `day10_analysis_*.md`, `day12_analysis_localhost.md`, `day13_analysis_ollama.md`,
> `day14_analysis_demo.md` — Day 14's full demo flow with a mixed analysis.
---

### Phase 3 — Windows Event Log pipeline (Days 15–19): no admin needed

The safest, most demo-impressive part — **no admin rights, no pywin32** thanks to
the built-in `--sample` corpus (schema-identical to real logs).

```powershell
# 3a. Read the sample log + threat summary (no LLM)
.\venv\Scripts\python.exe sentinelai.py logs --sample --json

# 3b. Save the sample as analysis-ready JSON, then analyze it
.\venv\Scripts\python.exe sentinelai.py logs --sample -o events.json
.\venv\Scripts\python.exe sentinelai.py analyze -i events.json --kind events --llm ollama --mode standard

# 3c. One command: sample -> LLM analysis (remediation mode makes a great demo)
.\venv\Scripts\python.exe sentinelai.py logs --sample --analyze --llm ollama --mode remediation

# 3d. Filter by real Security event IDs (e.g. failed logons 4625)
.\venv\Scripts\python.exe sentinelai.py logs --sample --event-ids 4625 --analyze --llm ollama
```

**Real logs (only if you have admin + pywin32):**
```powershell
.\venv\Scripts\python.exe sentinelai.py logs --hours 24 --analyze --llm ollama
```

**Raw CSV/EVTX export → analysis (this is the Day 19–21 parser):**
```powershell
# There's a sample export in the repo you can try right now:
.\venv\Scripts\python.exe -m sentinelai.cli parse -i day19_sample_export.csv --logs -o parsed_events.json
.\venv\Scripts\python.exe sentinelai.py analyze -i parsed_events.json --kind events --llm ollama
```

**What you should see:** `Threat level: MEDIUM/HIGH`, alert lines, then either the
short summary (3a) or the full 5-section LLM analysis (3b/3c). Real exports from
Event Viewer → "Save All Events As … CSV" drop straight in.

> Existing sample outputs you can compare:
> `day15_analysis_events.md`, `day16_analysis_*`, `day17_*_remediation*.md`,
> `day19_analysis_real.md`, `day21_analysis_autodetect.md`.
---

### Phase 4 — Reports & polish (Days 22–30): turn data into documents

```powershell
# Generate a report from any scan JSON (text / json / csv formats)
.\venv\Scripts\python.exe sentinelai.py report -i scan_results.json -o my_report --format text
.\venv\Scripts\python.exe sentinelai.py report -i scan_results.json -o my_report --format json
.\venv\Scripts\python.exe sentinelai.py report -i scan_results.json -o my_report --format csv

# If you don't pass -i, it picks the most recent scan_*.json automatically
.\venv\Scripts\python.exe sentinelai.py report -o my_report --format text
```

**What you should see:** `[+] Saved report to my_report.txt/.json/.csv`. Open the
CSV — it has one row per open port (IP, Protocol, Port, State, Service, Product,
Version). This is Suraj's module, hardened on Day 25 to accept **both** Week-1 and
Week-2 scan schemas (that was a real bug the E2E caught!).

> **Note:** the sprint's multi-format DOCX/PDF/MD report generator lives in
> `report_generator.py` (Suraj's module, merged Day 29) — see the modules section.

---

### Phase 5 — Interactive mode & the "one command" flow

```powershell
# Interactive natural-language CLI (Day 14)
.\venv\Scripts\python.exe sentinelai.py natural-cli
#   > scan localhost quickly
#   > network
#   > help
#   > exit
```

Then the **one-command end-to-end pipeline** (the Day 25 headline — this is the
whole Loop you've been walking, automated):

```powershell
.\venv\Scripts\python.exe tests/test_e2e_pipeline.py                # root CLI, live scan, ollama (~2 min)
.\venv\Scripts\python.exe tests/test_e2e_pipeline.py --skip-llm     # fast: scan + logs + report only
.\venv\Scripts\python.exe tests/test_e2e_pipeline.py --cli both     # validate BOTH entry points
```

Expect: `PASS 1/4 SCAN · PASS 2/4 LOGS · PASS 3/4 AI · PASS 4/4 REPORT`.

---

### Phase 6 — Offline test suites (prove everything, no network)

```powershell
.\venv\Scripts\python.exe -m pytest tests/ -q         # full suite (115+ tests)
.\venv\Scripts\python.exe -m pytest tests/test_ui.py tests/test_routing.py tests/test_log_parser.py tests/test_cli_sync.py -q
.\venv\Scripts\python.exe tests/demo_rehearsal.py     # the timed demo gate (~110s/180s)
```

**Optional live demo rehearsal** (the Day 27–30 script) — see `DEMO_SCRIPT.md`.
---

## 4. Teammates' modules you can also exercise (from `main`, Day 29 merge)

These are standalone helper modules (not CLI commands) — they power the pipeline
and are all covered by pytest. Quick Python one-liners (run from the repo root in
the venv):

```python
# Mapping a finding to OWASP / MITRE (Sneha)
from framework_mapper import map_to_owasp, map_to_mitre, map_keyword
print(map_to_owasp("sql injection"))
print(map_to_mitre("phishing"))
print(map_keyword("brute force"))

# Remediation for a finding (Sneha)
from remediation_mapper import get_remediation_for_findings
print(get_remediation_for_findings([{"name": "SQL injection", "category": "OWASP"}]))
```

```python
# CVE lookup (Suraj) - needs network (NVD API)
from cve.cve_lookup import lookup_cve   # pass a CVE ID
from cve.cve_search import search_cves  # pass a keyword
print(lookup_cve("CVE-2021-44228"))

# Multi-format report generation (Suraj)
from report_generator import generate_report
md = generate_report(findings=[...], analysis="...", report_format="markdown")
print(md[:200])
```

```python
# Full pipelines (end-to-end helper entry points)
from nmap_report_pipeline import run_nmap_to_report       # nmap_output -> report
from event_log_report_pipeline import run_event_log_to_report
```

---

## 5. Troubleshooting & gotchas (learned the hard way across Days 1–30)

| Symptom | Likely cause | Fix |
|---|---|---|
| `[!] Scan failed …` | Nmap not installed / not on PATH | `nmap --version`; run from an admin shell or add Nmap to PATH |
| `Analyze failed: …` on `--llm gemini` | No `GEMINI_API_KEY` in `.env` | `copy .env.example .env`, paste key |
| `Analyze failed: …` on `--llm ollama` | Ollama not running, or model missing | `ollama serve` then `ollama pull llama3` (once) |
| Long local-model analysis | Ollama is single-model on this box | run analyses **sequentially** (known ops note, Day 21) |
| `logs` without `--sample` says admin needed | Real Security log needs admin + pywin32 | use `--sample`, or run the terminal as Administrator |
| Terminal shows the panel as plain text | Non-TTY (piped) output | that's by design; run interactively for Rich boxes |
| `report` "No scan JSON files found" | No `scan_*.json` in cwd | run a scan first, or pass `-i <file>` |

---

## 6. The 3-minute demo that ties it all together

If you want one living demonstration of the whole thing (judge-style):

1. `sentinelai.py network` (5s)
2. `sentinelai.py scan --target 127.0.0.1 --fast --json-file scan_results.json` (~30s)
3. `sentinelai.py logs --sample --analyze --llm ollama --mode remediation` (~60s, local AI)
4. `sentinelai.py analyze -i scan_results.json --llm ollama --no-save` (~40s)
5. `sentinelai.py report -i scan_results.json -o final_report --format text` (instant)

Under 3 minutes, zero crashes, and you've touched Scan → Logs → AI → Report.
That exact recipe is what `tests/demo_rehearsal.py` gates at **110.5s / 180s**.

---

## What's *not* here (yet)

- **Active testing / ZAP** (`--active`) — that's the Feature Sprint you and the
  team are building now, Days 31–44 (`sentinelai/consent.py` already landed on
  Day 32). It will bolt onto Phase 1 as an extra `--active` flag with the consent gate.
- **OpenAI/Claude** providers are accepted but intentionally unwired (free-first
  design; they fail with friendly guidance instead of charging).

---

*Happy testing — scan → logs → AI → report, one command, under three minutes, zero crashes.* 🛡️
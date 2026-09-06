# SentinelAI — Hackathon Demo Script

> **Goal:** full scan + logs + AI + report story in **under 3 minutes, zero crashes**.
> Gate enforced by `python tests/demo_rehearsal.py` (Day 27 rehearsal tool).
> Suggested split: **~2:10 of commands + ~0:30 of talking.**

---

## T-minus 10 minutes — pre-demo checklist

- [ ] `venv\Scripts\activate` (correct venv!)
- [ ] Ollama running **and warm**: `ollama list` shows `llama3` (or `gemma4`), then `ollama run llama3 "ping"` once so the model is loaded into VRAM (cold start can eat 30–60s)
- [ ] `nmap --version` works (scanning step depends on it)
- [ ] Admin terminal **not** required — every demo command works without elevation (`--sample` events)
- [ ] Terminal font large, notifications silenced, repo at a clean commit
- [ ] Fallbacks ready (see bottom): committed `scan_results.json` fixture + `day19_sample_export.csv` if live scanning is blocked

---

## The flow (5 steps)

| Step | Time budget | Command |
|---|---|---|
| 1. Intro + target | 0:20 | `python sentinelai.py network` |
| 2. Scan | 0:20 | `python sentinelai.py scan --target 127.0.0.1 --fast --json-file demo_scan.json` |
| 3. Event-log wow (local Ollama) | 1:10 | `python sentinelai.py logs --sample --analyze --llm ollama` |
| 4. Scan analysis (cloud Gemini) | 0:25 | `python sentinelai.py analyze -i demo_scan.json --kind scan --llm gemini -o demo_analysis.md` |
| 5. Report + close | 0:15 | `python sentinelai.py report -i demo_scan.json -o demo_report --format text` |

> **Why two providers?** It demonstrates the Day 21 routing story *and* keeps the demo under 3 minutes: the sensitive event-log leg stays on **local Ollama** (private), the shareable scan report goes through **cloud Gemini** (~5–15 s vs ~90–115 s on the local 8B model). Measured: both-on-Ollama = 226.8 s (**over** the gate — caught by the Day 27 rehearsal); Ollama+Gemini split fits comfortably.

### Step 1 — Intro (0:20)

```bash
python sentinelai.py network
```

**Say:** "This is our own machine — hostname, local IP — and that's today's target. SentinelAI is a defensive-security CLI that turns raw scan data and Windows Event Logs into an analyst-grade report using free LLMs — Gemini in the cloud, or Ollama fully local."

### Step 2 — Scan (0:40)

```bash
python sentinelai.py scan --target 127.0.0.1 --fast --json-file demo_scan.json
```

**Point at:** the spinner while nmap runs, then the Rich panel with the scan summary.
**Say:** "One command wraps Nmap, parses the output into structured JSON — hosts, ports, services, versions. `--fast` is the top-20-ports profile; there's also standard and aggressive. The JSON file is what the LLM will consume, and `--json` alone gives pipe-clean machine output."

### Step 3 — Event-log wow moment (1:00)

```bash
python sentinelai.py logs --sample --analyze --llm ollama
```

**Point at:** "Read 3 event(s) from sample", threat level, alerts — then the 5-section LLM analysis rendering as Markdown.
**Say:** "This is a Windows Security log — here a **failed logon burst (Event 4625)**, which the engine maps to **MITRE ATT&CK T1110 Brute Force**; **account creation (4720)** maps to **T1136**. The sample corpus means this works with no admin rights — swap in the real Security log and it's the same pipeline. And because this runs on **local Ollama, sensitive log data never leaves this machine** — that's our `--routing private` policy; `--routing report` sends shareable reports through Gemini instead."

### Step 4 — Scan analysis (0:25)

```bash
python sentinelai.py analyze -i demo_scan.json --kind scan --llm gemini -o demo_analysis.md
```

**Point at:** the saved `demo_analysis.md`.
**Say:** "Same unified engine, now on the scan — this leg routes through **cloud Gemini** via our `--routing report` policy, because a scan report is meant to be shared. Strict five-section output: executive summary, findings ranked by risk, risk assessment, recommendations, next steps — saved as Markdown, ready to paste into a ticket."
*(No key on the demo machine? Run it with `--llm ollama` and let the spinner ride, or show the committed analysis artifact — but expect ~95 s instead of ~15 s.)*

### Step 5 — Report + close (0:15)

```bash
python sentinelai.py report -i demo_scan.json -o demo_report --format text
```

**Say:** "And a classic text/JSON/CSV report for the compliance folks. One command, scan to report — that's SentinelAI."

---

## MITRE ATT&CK quick reference (for Q&A)

| Windows Event | Meaning | MITRE mapping |
|---|---|---|
| 4624 | Successful logon | T1078 — Valid Accounts |
| 4625 | Failed logon (burst = brute force) | T1110 — Brute Force |
| 4720 | Account created | T1136 — Create Account |
| 4726 | Account deleted | T1531 — Account Access Removal |

The catalog lives in `sentinelai/event_logs.py` (`CRITICAL_SECURITY_EVENTS`) with ~20 monitored IDs; detection heuristics (brute force, account changes, unusual access) run **before** the LLM so the model gets pre-digested findings, not raw noise.

## If something goes wrong live (fallbacks)

| Failure | Fallback |
|---|---|
| Ollama cold/slow | It was warmed in the checklist; worst case the spinner shows progress — narrate the routing story while it loads |
| Ollama down | `--llm gemini` (needs `GEMINI_API_KEY` in `.env`), or narrate over the committed analysis artifacts |
| Nmap blocked (Wi-Fi captive portal etc.) | Use the committed fixture: `python sentinelai.py analyze -i scan_results.json --kind scan --llm ollama` |
| Admin prompt appears | It won't — all demo commands run unelevated (`--sample` events) |

## Rehearsal evidence (Day 27)

Tool: `python tests/demo_rehearsal.py` — preflight (Ollama reachable, models present, key check, nmap on PATH, CLI starts) → runs the five steps above in a sandbox, times each, validates artifacts (scan JSON schema, JSON-pure log output, 5-section analysis, report banner) and enforces the 180 s budget.

**Measured runs (Day 27, live):**

| Run | Flow | Result |
|---|---|---|
| 1 — both LLM legs on Ollama | scan 6.6s · logs 6.1s · logs-AI **115.7s** · scan-AI **95.0s** · report 3.4s | ❌ **226.8s — OVER the gate** (zero crashes, though) |
| 2 — Ollama (private) + Gemini (report) | scan 2.8s · logs 2.3s · logs-AI **58.7s** · scan-AI **38.3s** · report 2.4s | ✅ **104.5s — PASSED**, 75 s spare |

**Finding (→ fixed same day):** the both-local flow busts the 3-minute sprint gate purely on local-model generation time. The demo now showcases the `--routing` story instead — private event-log leg on local Ollama, shareable scan report on cloud Gemini — cutting the total by 2×+ while **demonstrating more features**.


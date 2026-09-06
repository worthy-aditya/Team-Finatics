# Week 2 — Day 14: Team Sync — Full Pipeline Demo (Scan → LLM → Analysis)
**Date:** 2026-08-26
**Developer:** Aditya Gupta (Project Lead & LLM)
**Sprint:** SentinelAI 30-Day Sprint | Week 2, Day 14
**Status:** ✅ **COMPLETE — WEEK 2 MILESTONE MET**

---

## Day 14 Objective
> Team sync — full demo of scan → LLM analysis pipeline
> **Deliverable:** A repeatable one-command demo plus a presenter cheat-sheet, proving the Week 2 milestone end-to-end with both FREE providers

---

## What Was Built

### 1. One-Command Pipeline Demo (`demo_day14_pipeline.py`)
Runs the entire Week 2 pipeline in a single invocation:

```
Nmap scan (localhost, ~11s) → day14_scan_demo.json
      ↓
refined 5-section prompt → analyze_scan_data(provider=...)
      ↓
programmatic section verification (5/5 required)
      ↓
day14_analysis_demo.md  + summary box (wall time, provider/model)
```

- `--provider gemini|ollama` — switch brains with one flag (free providers only)
- `--skip-scan` / `--rescan` — instant rerun vs forced fresh scan
- Resume-safe; fails loudly if any required section is missing

### 2. Presenter Cheat-Sheet (`DEMO_DAY14_SCRIPT.md`)
Everything needed to run the sync without surprises:
- Pre-demo checklist (venv, nmap, ollama warm-up, key present)
- Option A one-command flow + Option B manual stage-by-stage CLI tour
- 30-second pitch, expected timings table, **fallback plans** (wifi dies → local ollama; quota → flag flip; cold model → pre-warm), anticipated Q&A

### 3. Fix Found During Validation
Port-summary line initially parsed the wrong JSON schema (`scan.tcp` raw
python-nmap style). Corrected to NmapScanner's structured schema
(`hosts[].ports[]`, filtering `state=="open"`).

---

## Live Validation Results ✅

Full pipeline (fresh scan → ollama):
```
[+] Scan done in 11.5s -> day14_scan_demo.json
[+] Parsed 1 host(s), open TCP ports: ['135/msrpc', '445/microsoft-ds']
[*] Analyzing with provider=ollama (mode=standard) ...
[+] Analysis OK in 74.4s via gemma4:latest (prompt=1909 tok, response=1968 tok)

PIPELINE COMPLETE — Total wall time: 85.9s   (5/5 sections verified)
Provider/Model  : ollama / gemma4:latest
```

Offline test suite still green:
```
$ python tests/test_prompt_engine.py
ALL prompt_engine TESTS PASSED (offline, pure functions)
```

Artifacts: `day14_scan_demo.json` · `day14_analysis_demo.md` (7.7 KB)

---

## Week 2 Milestone Scoreboard

| Sprint deliverable | Status |
|--------------------|--------|
| Nmap wrapper integrated as `scan` command (Day 8) | ✅ |
| AI plain-English analysis via Gemini free tier (Day 9) | ✅ |
| Refined risk-focused prompt, 3 validated scans (Day 10) | ✅ |
| Reusable prompt-engineering module (Day 11) | ✅ |
| Ollama local/private LLM support (Day 12) | ✅ |
| `--llm` switcher across providers (Day 13) | ✅ |
| Repeatable full-pipeline team demo (Day 14) | ✅ |

**Week 2 goal "Nmap scans + AI plain-English analysis": MET.**

---

## Ready for Week 3 (Days 15-21)

- Windows Event Log ingestion + LLM analysis (Affan + Aditya)
- OWASP Top 10 / MITRE ATT&CK mapping layer (Sneha)
- DOCX/PDF/Markdown reports, CVE/NVD lookup (Suraj)
- Beginner mode (`--beginner`) reuses `PromptMode.BEGINNER` from Day 11

---

## Sign-Off

**Day 14 Status:** ✅ **COMPLETE AND VALIDATED**

- ✅ One-command E2E demo passing live (85.9 s total, 5/5 sections)
- ✅ Presenter cheat-sheet with fallback plans for every failure mode
- ✅ Both free providers demoable through one flag

**Developer:** Aditya Gupta
**Completion Date:** 2026-08-26
**Team:** Team Finatics | CodeQuest 4.0
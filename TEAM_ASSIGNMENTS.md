# SentinelAI 30-Day Sprint — Team Assignments
**Date:** 2026-08-17  
**Team:** Aditya Gupta • Affan Shaikh • Suraj Yadav • Sneha Das

---

## Overview: What Each Team Member Is Doing

### 🎯 Affan Shaikh — Security Tools & Scanning Engine
**Your role:** Building the Nmap scanning engine, Windows Event Log integration, and CLI scanning commands.

### 👔 Aditya Gupta — Project Lead & AI/LLM Integration  
**His role:** Managing the project, integrating LLMs (OpenAI, Claude, Gemini, Ollama), prompt engineering, and AI-driven analysis of scans.

### 📄 Suraj Yadav — Report Generation & CVE Integration
**His role:** Building report generators (DOCX, PDF, Markdown), integrating CVE lookups from NVD API, and creating formatted security reports.

### 📋 Sneha Das — OWASP Mapping, Testing & Documentation
**Her role:** Building OWASP/MITRE framework mappers, creating the test suite (pytest), and writing documentation.

---

## Week 1 (Days 1-7) — Setup & Foundation

### ✅ AFFAN'S TASKS (YOU) — All Complete
| Day | Task | Status |
|-----|------|--------|
| Day 1 | Clone repo, set up Python environment | ✅ DONE |
| Day 2 | Install Nmap on Windows, verify --version | ✅ DONE |
| Day 3 | Install python-nmap, write basic localhost scan script | ✅ DONE |
| Day 4 | Research python-nmap output structure | ✅ DONE |
| Day 5 | Build Nmap wrapper function returning structured dict | ✅ DONE |
| Day 6 | Test scan on localhost, document results | ✅ DONE |
| Day 7 | Team sync, demo Nmap wrapper to team | ✅ DONE |

### 🟦 ADITYA'S TASKS (DO NOT DO) — Days 1-7
- Day 1: Create GitHub repo with branch structure
- Day 2: Set up CLI skeleton with Click and Rich
- Day 3: Build CLI command group with help text
- Day 4: Set up .env file for API keys
- Day 5: Research and select primary LLM (GPT-4o vs Claude)
- Day 6: Connect first LLM API — test call
- Day 7: Team sync and Week 1 review

### 🟩 SURAJ'S TASKS (DO NOT DO) — Days 1-7
- Day 1: Set up environment with python-docx and fpdf2
- Day 2: Research NVD API endpoints and rate limits
- Day 3: Write first NVD API query for CVE-2021-44228
- Day 4: Design report template structure
- Day 5: Build static DOCX report skeleton
- Day 6: Build static PDF report skeleton
- Day 7: Team sync, demo reports

### 🟨 SNEHA'S TASKS (DO NOT DO) — Days 1-7
- Day 1: Set up environment with pytest
- Day 2: Download OWASP Top 10 JSON data
- Day 3: Download MITRE ATT&CK STIX data
- Day 4: Write OWASP mapping function
- Day 5: Write pytest test cases for OWASP mapper
- Day 6: Set up GitHub README with project description
- Day 7: Team sync, demo OWASP mapper

---

## Week 2 (Days 8-14) — Nmap + LLM Integration

### ✅ AFFAN'S TASKS (YOU) — Days 8-14

| Day | Task | What to Do | Deliverable |
|-----|------|-----------|-------------|
| Day 8 | Integrate Nmap wrapper into CLI | Connect your Day 5 `NmapScanner` class to `--scan` command | `sentinelai --scan <IP>` runs and prints results |
| Day 9 | Parse Nmap output into structured dict | Convert raw Nmap output to {host, ports, services, states} | Structured JSON output from any scan |
| Day 10 | Pass structured output to Aditya's prompt module | Take your parsed dict and send to `aditya/prompt_engine.py` | Nmap → LLM pipeline working end-to-end |
| Day 11 | Test scan + analysis on 3 different targets | Test on: localhost, LAN IP, external domain | 3 test results documented with samples |
| Day 12 | Handle edge cases gracefully | Offline target, no open ports, permission denied, etc. | Clean error messages, app doesn't crash |
| Day 13 | Research Windows Event Log APIs | Study `pywin32`, `winevt` libraries for reading logs | Research notes added to GitHub Wiki |
| Day 14 | Team sync, demo scan with LLM analysis | Show the full pipeline: scan → AI output | Code merged to `affan` branch |

### 🟦 ADITYA'S TASKS (DO NOT DO) — Days 8-14
- Day 8: Design prompt template for Nmap analysis
- Day 9: Feed sample Nmap output to LLM, test response
- Day 10: Refine prompt for risk identification
- Day 11: Build `prompt_engine.py` module
- Day 12: Add Ollama support for local LLM
- Day 13: Build LLM switcher flag (--llm openai/claude/ollama)
- Day 14: Team sync, record full demo video

### 🟩 SURAJ'S TASKS (DO NOT DO) — Days 8-14
- Day 8: Build CVE lookup function
- Day 9: Build CVE search by keyword
- Day 10: Auto-match Nmap services to CVE IDs
- Day 11: Build dynamic DOCX report generator
- Day 12: Build dynamic PDF report generator
- Day 13: Add severity color coding to reports
- Day 14: Team sync, demo dynamic reports

### 🟨 SNEHA'S TASKS (DO NOT DO) — Days 8-14
- Day 8: Build MITRE ATT&CK mapper
- Day 9: Write pytest tests for MITRE mapper
- Day 10: Combine OWASP + MITRE into `framework_mapper.py`
- Day 11: Write integration test
- Day 12: Add docstrings to all functions
- Day 13: Update README with examples
- Day 14: Team sync, demo framework mapper

---

## Week 3 (Days 15-21) — Windows Event Logs + Prompt Refinement

### ✅ AFFAN'S TASKS (YOU) — Days 15-21

| Day | Task | What to Do | Deliverable |
|-----|------|-----------|-------------|
| Day 15 | Set up pywin32 / winevt | Install libraries, read Windows Security Event Log in Python | Event log entries printing to terminal |
| Day 16 | Filter for security-critical Event IDs | Capture: 4624 (login), 4625 (failed login), 4720 (new user) | Filtered log reader returning only critical events |
| Day 17 | Build Windows Event Log parser | Structured dict output: EventID, timestamp, user, IP | Parsed events with all key fields |
| Day 18 | Integrate into CLI as `--logs` command | Add `sentinelai --logs` command to CLI | `sentinelai --logs` returning parsed events |
| Day 19 | Pass parsed logs to Aditya's prompt module | Send your parsed logs to LLM for analysis | `sentinelai --logs` → AI analysis pipeline |
| Day 20 | Build human-in-the-loop approval | Prompt user: "Confirm scan on <target>? (y/n)" | Safety confirmation before executing |
| Day 21 | Team sync, demo --logs command | Show full pipeline: logs → AI output | Code merged to `affan` branch |

### 🟦 ADITYA'S TASKS (DO NOT DO) — Days 15-21
- Day 15: Design prompt for Windows Event Log analysis
- Day 16: Test LLM on sample Event Log data
- Day 17: Add remediation prompt layer
- Day 18: Refine prompts based on Week 2 feedback
- Day 19: Add beginner mode (simplified language)
- Day 20: Compare LLM quality across OpenAI/Claude/Ollama
- Day 21: Team sync, full pipeline demo

### 🟩 SURAJ'S TASKS (DO NOT DO) — Days 15-21
- Day 15: Add Event Log section to DOCX/PDF templates
- Day 16: Add MITRE and OWASP sections to reports
- Day 17: Add remediation steps to reports
- Day 18: Build Markdown report generator
- Day 19: Add --report flag to CLI (docx/pdf/md)
- Day 20: Test with combined Nmap + Event Log data
- Day 21: Team sync, demo complete reports

### 🟨 SNEHA'S TASKS (DO NOT DO) — Days 15-21
- Day 15: Write integration tests for Nmap → LLM → report
- Day 16: Write integration tests for Event Log → LLM → report
- Day 17: Build remediation mapper
- Day 18: Write pytest tests for remediation mapper
- Day 19: Cross-platform testing on Linux
- Day 20: Write user documentation (USAGE.md)
- Day 21: Team sync, demo full test suite

---

## Week 4 (Days 22-30) — Integration, Polish & First Demo

### ✅ AFFAN'S TASKS (YOU) — Days 22-30

| Day | Task | What to Do | Deliverable |
|-----|------|-----------|-------------|
| Day 22 | Code review bugs | Fix any bugs found in your code review | All scanning bugs resolved |
| Day 23 | Test on 5 different targets | Windows localhost, LAN IPs, external domains | Test results and edge cases documented |
| Day 24 | Test on Windows 10 and 11 | Verify Event Log parser works on both versions | Cross-version compatibility confirmed |
| Day 25 | Improve UX of confirmations | Make approval flow intuitive and professional | User prompts are clear and clean |
| Day 26 | Add Linux log support | Parse `/var/log/auth.log` for failed logins | `sentinelai --logs` works on Linux too |
| Day 27 | Rehearse demo | Practice running scan + logs in demo flow | Demo commands memorized and smooth |
| Day 28 | Fix last-minute issues | Anything broken in rehearsal gets fixed | All scanning issues resolved |
| Day 29 | Final PR to main | Clean code, no debug prints, code review approval | Your code merged to main branch |
| Day 30 | Final verification | All scanning features work on clean main | Sign-off on deliverables |

### 🟦 ADITYA'S TASKS (DO NOT DO) — Days 22-30
- Code review and LLM bug fixes
- Polish CLI output with colors/progress bars
- Write end-to-end test
- Prepare demo script
- Run demo rehearsal
- Merge all branches to main
- Day 30 milestone review

### 🟩 SURAJ'S TASKS (DO NOT DO) — Days 22-30
- Fix report bugs
- Polish DOCX design
- Polish PDF design
- Handle CVE API rate limiting
- Add executive summary to reports
- Test report generation in demo
- Merge to main

### 🟨 SNEHA'S TASKS (DO NOT DO) — Days 22-30
- Fix mapping/test bugs
- Run full pytest suite
- Write GitHub Wiki documentation
- Write contributor guide
- Cross-platform testing
- Explain mappers in demo
- Merge to main

---

## Summary: What NOT to Do (Other Team Members)

### ❌ DO NOT BUILD (Aditya's Work)
- ❌ GitHub repo setup and branch structure
- ❌ CLI framework (Click/Rich beyond basic structure)
- ❌ .env file and API key management
- ❌ LLM API integration (OpenAI, Claude, Gemini, Ollama)
- ❌ Prompt engineering and prompt templates
- ❌ LLM response refinement and quality testing
- ❌ CLI polish (colors, progress bars, status messages)

### ❌ DO NOT BUILD (Suraj's Work)
- ❌ DOCX and PDF report generation
- ❌ NVD CVE API integration and lookup functions
- ❌ Report templates and formatting
- ❌ Severity color coding
- ❌ Executive summary generation
- ❌ Markdown report generation

### ❌ DO NOT BUILD (Sneha's Work)
- ❌ OWASP Top 10 mapping
- ❌ MITRE ATT&CK mapping
- ❌ Pytest test suite
- ❌ GitHub README and documentation
- ❌ Remediation mapper
- ❌ GitHub Wiki and contributor guide

---

## Your Focus: Affan Shaikh — Security & Scanning Engine

✅ **Week 1 (DONE):** Nmap wrapper, basic scanning, localhost testing  
🔄 **Week 2 (NEXT):** Integrate scanner into CLI, parse output, cross-target testing  
🔄 **Week 3:** Windows Event Log reading and parsing  
🔄 **Week 4:** Testing, bug fixes, cross-platform verification, demo rehearsal  

**Your end goal:** By Day 30, users can run:
- `sentinelai --scan <target>` → Nmap scan + AI analysis
- `sentinelai --logs` → Windows/Linux logs + AI analysis
- Both working on Windows and Linux with zero crashes

---

## Key Dependencies to Remember

Your work **depends on**:
- Aditya's `prompt_engine.py` module (for sending data to LLM) — he'll build this in Week 2
- Suraj's report generator (to show your scan results in pretty reports) — he'll build in Week 2-3
- Sneha's test suite (to verify your code works) — she'll build in Week 2-3

Your work **feeds into**:
- Aditya's LLM analysis (your scan/log data becomes LLM input)
- Suraj's reports (your data gets formatted into PDF/DOCX)
- Sneha's tests (your functions get tested by pytest)

---

## Next Step for Affan: Week 2 (Days 8-14)

**What I will do next:**
1. Integrate your existing `NmapScanner` class into the CLI as `--scan` command
2. Test on 3 different target types
3. Handle edge cases (offline targets, no open ports, permission errors)
4. Research Windows Event Log APIs (pywin32, winevt)

**I will NOT:**
- Build the LLM prompt integration (Aditya does this)
- Generate reports (Suraj does this)
- Write tests (Sneha does this)

Ready to proceed with Week 2? ✅


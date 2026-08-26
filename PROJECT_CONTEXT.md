# SentinelAI CLI — Project Context

**Team:** Team Finatics | **Competition:** CodeQuest 4.0 | **Date:** July 2026
**Members:** Aditya Gupta (Lead/LLM) • Affan Shaikh (Scanning) • Suraj Yadav (Reports/CVE) • Sneha Das (Mapping/Testing/Docs)

---

## 1. Project Overview

**SentinelAI CLI** is an AI-powered cybersecurity CLI agent that:
- Runs Nmap network scans and parses structured output
- Sends scan data to LLMs (Gemini, OpenAI, Claude, Ollama) for plain-English security analysis
- Maps findings to MITRE ATT&CK and OWASP Top 10 frameworks
- Cross-references CVEs via NVD API
- Generates professional reports (DOCX, PDF, Markdown)
- Provides a natural-language CLI interface for beginners

**Tagline:** *Learn. Analyze. Secure.*

---

## 2. Vision & Differentiation

- **Target user:** Cybersecurity students, small IT teams, security professionals
- **Unique position:** Only tool combining defensive focus + Windows support + plain-English explanations + MITRE/OWASP mapping + auto report generation
- **Competitors:** Microsoft Security Copilot (enterprise-only, $57+/mo), PentestGPT, METATRON, CAI, PentAGI (all offensive-only, Linux-only)
- **Key differentiators:** Defensive-first, cross-platform (Windows + Linux), beginner mode, human-in-the-loop safety, local Ollama support for privacy

---

## 3. Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Language | Python 3.8+ | Primary language |
| CLI Framework | Click 8.3.1 + Rich 15.0.0 | Command parsing + colored output |
| Scanning | python-nmap 0.7.1 | Nmap integration |
| LLM APIs | Google Gemini (google-genai 2.13.0), OpenAI, Anthropic Claude | AI analysis |
| Local AI | Ollama (planned) | Offline/privacy mode |
| Config | python-dotenv 1.2.3 | API key management |
| Reporting | python-docx, fpdf2 (planned) | DOCX/PDF reports |
| Testing | pytest (planned) | Unit/integration tests |
| Version Control | Git + GitHub | Collaboration |

---

## 4. Project Structure

```
Team-Finatics/
├── sentinelai.py              # Main CLI entry point (Click group)
├── setup.py                   # Package configuration
├── requirements.txt           # All dependencies
├── .env.template              # API key template (OPENAI/CLAUDE/GEMINI)
├── .gitignore                 # Python/venv ignore rules
├── sentinelai/
│   ├── __init__.py            # Package init (exports Scanner)
│   ├── cli.py                 # Click CLI: scan, analyze, natural-cli, version
│   ├── scanner.py             # Scanner base + NmapScanner class
│   ├── prompt_engine.py       # Gemini LLM analysis + prompt templates
│   └── natural_cli.py         # Natural language command interpreter
├── commands/
│   ├── __init__.py            # Empty package init
│   ├── scan.py                # scan command (Nmap wrapper)
│   ├── network.py             # network info command
│   ├── report.py              # report generation (text/json/csv)
│   ├── analyze.py             # analyze command (LLM analysis)
│   └── natural_cli.py         # natural-cli command wrapper
├── scan_localhost.py          # Basic Nmap scan script (subprocess)
├── demo_natural_cli.py        # Natural CLI demo script
├── test_natural_cli.py        # Natural CLI parsing tests
├── test_nmap_analysis.py      # Day 9 LLM analysis test
├── scan_results.json          # Sample scan output (localhost)
├── scan_report.txt            # Sample text report
├── day9_nmap_llm_analysis.md  # Day 9 LLM analysis output
└── *.md / *.docx              # Documentation & reports
```

---

## 5. Core Code Files — Key Details

### sentinelai/scanner.py
- **Scanner** base class: `validate_target()` (IPv4/domain/localhost regex), `scan()`, `get_results()`
- **NmapScanner** class:
  - `scan(arguments="-sV -p 1-1000")` → executes Nmap via python-nmap
  - `parse_results()` → structured dict with metadata, summary, hosts, ports, services
  - `get_open_ports()` → list of open ports with service details
  - `get_summary()` → human-readable formatted output
  - `export_json(filepath)` → saves results to JSON
  - `to_json_string()` / `get_json_dict()` → programmatic access

### sentinelai/prompt_engine.py
- `NMAP_ANALYSIS_PROMPT` → template asking LLM for: summary, risk findings, attacker perspective, next steps
- `load_scan_data(path)` → loads JSON scan file
- `build_nmap_analysis_prompt(scan_data)` → formats prompt with scan data
- `generate_nmap_analysis(scan_data, preferred_model)` → calls Gemini with fallback models
- `analyze_scan_file(input_file, output_file, preferred_model)` → full analysis flow
- **Day 11 additions:** `build_prompt(scan_data, mode)` dispatcher (STANDARD/
  BEGINNER/REMEDIATION templates), `analyze_scan_data(provider, mode, ...)`
  unified entry point returning `ScanAnalysisResult`, `LLMProvider` +
  `PromptMode` enums, `default_models_for_provider()` with env overrides,
  `_call_gemini()` internal helper with token usage capture
- Default models: `gemini-3.6-flash`, `gemini-flash-latest`, `gemini-3.5-flash`, `gemini-3.7-flash`
- Requires `GEMINI_API_KEY` in `.env`

### sentinelai/cli.py
- `main` Click group with commands: `scan`, `analyze`, `natural_cli`, `version`
- `scan` command: `--target`, `--aggressive`, `--fast`, `--timeout`, `--json`, `--json-file`
- `analyze` command: `--input`, `--output`, `--model`, `--no-save`

### sentinelai/natural_cli.py
- `NaturalLanguageCLI` class with `parse_intent()`, `execute_command()`, `run_interactive()`
- Uses Claude/Gemini for intent parsing, falls back to regex-based `_simple_parse()`
- Supports actions: scan, analyze, report, network, help, exit
- Scan types: fast (20 ports), standard (1000 ports), aggressive (full + scripts)

### commands/report.py
- Generates text, JSON, and CSV reports from scan JSON files
- Auto-detects most recent scan file if no input specified

---

## 6. 30-Day Sprint Plan

| Week | Days | Focus | Milestone |
|------|------|-------|-----------|
| **Week 1** | 1-7 | Setup & Foundation | GitHub live, dev environments, CLI skeleton |
| **Week 2** | 8-14 | Nmap + LLM Integration | Nmap scans + AI plain-English analysis |
| **Week 3** | 15-21 | Windows Event Logs + Prompts | Log ingestion + prompt refinement |
| **Week 4** | 22-30 | Integration & First Demo | All features connected end-to-end |

### Team Roles
| Member | Role | Day 30 Deliverable |
|--------|------|-------------------|
| **Aditya Gupta** | Project Lead & AI/LLM | CLI framework, LLM integration (OpenAI/Claude/Gemini/Ollama), prompt engineering, beginner mode, demo script |
| **Affan Shaikh** | Scanning Engine | Nmap integration, Windows Event Log parser, Linux auth.log parser, human-in-the-loop safety, `--scan` and `--logs` commands |
| **Suraj Yadav** | Reports & CVE | DOCX/PDF/Markdown reports, CVE NVD lookup, executive summary, severity color coding |
| **Sneha Das** | Mapping, Testing & Docs | OWASP Top 10 mapper, MITRE ATT&CK mapper, remediation mapper, full pytest suite, README/USAGE/CONTRIBUTING docs |

---

## 7. Implementation Status

### ✅ COMPLETED (Week 1 — Days 1-7)
- GitHub repo live with branch structure
- Python venv + dependencies installed
- Nmap 7.99 installed and verified on Windows
- CLI skeleton with Click + Rich working
- `.env` template committed (without actual keys)
- NmapScanner class fully built and tested on localhost
- Report generation (text/json/csv) working
- Natural Language CLI interface working
- README published

### ✅ COMPLETED (Week 2 — Days 8-10)
- **Day 8:** Nmap wrapper integrated into CLI as `scan` command
- **Day 9:** LLM analysis working — `prompt_engine.py` built with Gemini API
  - `day9_nmap_llm_analysis.md` shows successful analysis of localhost scan
  - Identified ports 135 (MSRPC) and 445 (SMB) as risks with remediation steps
- **Day 10:** Prompt refined — risk identification + next steps (3 test scans)
  - Refined `NMAP_ANALYSIS_PROMPT` to 5 strict sections: Summary, ranked Risk
    Findings (Severity X/10 + evidence), Attacker Perspective (defensive),
    Next Steps split into Immediate/Hardening, Confidence & Limitations
  - Reliability fixes in `prompt_engine.py`: IPv4-only resolution patch
    (google-genai IPv6 hang), 300s timeout, retry with backoff (429/500/503),
    updated model fallbacks to valid 2026 list, safety settings + defensive
    framing to prevent refusals on real-device scans
  - Validated with 3 test scans → `day10_analysis_localhost.md`,
    `day10_analysis_scanme.md`, `day10_analysis_gateway.md`
  - New wrapper: `test_day10_prompt_refinement.py`
  - Report: `WEEK_2_DAY_10_REPORT.md`
- **Day 11:** Prompt engineering module completed (reusable functions)
  - Prompt modes: `PromptMode` STANDARD / BEGINNER / REMEDIATION with
    `build_prompt(scan_data, mode=...)` dispatcher; backward-compatible
    `build_nmap_analysis_prompt()` alias
  - Provider abstraction: `LLMProvider` enum, `ScanAnalysisResult` dataclass,
    `default_models_for_provider()` with env overrides, unified
    `analyze_scan_data(provider=..., mode=...)` entry point ready for
    Day 12 Ollama + Day 13 `--llm` switcher
  - Gemini HTTP logic refactored into `_call_gemini()`; token usage captured
  - Offline unit tests: `tests/test_prompt_engine.py` (runs via pytest or
    plain script) — all passing
  - Report: `WEEK_2_DAY_11_REPORT.md`

### ⏳ PENDING (Week 2 — Days 12-14)
- [ ] Day 12: Add Ollama support — local Llama 3 via Ollama
- [ ] Day 13: Build LLM switcher — `--llm openai/claude/gemini/ollama` flag
- [ ] Day 14: Team sync — full demo of scan → LLM analysis pipeline

### ⏳ PENDING (Week 3 — Days 15-21)
- [ ] Day 15: Windows Event Log prompt template
- [ ] Day 16: Event Log → LLM analysis testing
- [ ] Day 17: Remediation prompt layer
- [ ] Day 18: Refine all prompts (v2)
- [ ] Day 19: Beginner mode (`--beginner` flag)
- [ ] Day 20: Compare LLM quality across providers
- [ ] Affan: pywin32/winevt setup, Event ID filtering (4624/4625/4720), `--logs` command
- [ ] Suraj: Event Log sections in reports, MITRE/OWASP sections, Markdown reports, `--report` flag
- [ ] Sneha: Integration tests, remediation mapper, cross-platform tests, USAGE.md

### ⏳ PENDING (Week 4 — Days 22-30)
- [ ] Code review and bug fixes across all branches
- [ ] CLI polish (colors, progress indicators, Rich library)
- [ ] End-to-end test (scan + logs + AI + report in one command)
- [ ] Demo script preparation
- [ ] Demo rehearsal (under 3 minutes, zero crashes)
- [ ] Merge all branches to main
- [ ] Day 30 milestone review and sign-off

---

## 8. Key Dependencies & Data Flow

```
User Input (CLI)
    ↓
sentinelai/cli.py (Click Commands)
    ↓
sentinelai/scanner.py (NmapScanner)
    ├─ scan() → Executes nmap via python-nmap
    ├─ parse_results() → Structured dict
    └─ export_json() → JSON file
    ↓
sentinelai/prompt_engine.py
    ├─ load_scan_data() → Reads JSON
    ├─ build_nmap_analysis_prompt() → Formats prompt
    └─ generate_nmap_analysis() → Gemini API call
    ↓
Plain-English Analysis (Markdown output)
```

**Team dependencies:**
- Affan's scan data → Aditya's LLM analysis → Suraj's reports → Sneha's tests
- Aditya's `prompt_engine.py` is the central integration point

---

## 9. Environment & Configuration

### Required API Keys (in `.env`)
```
OPENAI_API_KEY=your_openai_api_key_here
CLAUDE_API_KEY=your_claude_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

### Key Commands
```bash
# Scan
python sentinelai.py scan --target 127.0.0.1 --fast
python sentinelai.py scan --target 127.0.0.1 --aggressive

# Analyze with LLM
python sentinelai.py analyze --input scan_results.json

# Natural language CLI
python sentinelai.py natural-cli

# Network info
python sentinelai.py network

# Reports
python sentinelai.py report --format text|json|csv
```

---

## 10. Important Development Rules

1. **Do NOT modify application code** unless explicitly asked — this document is for context only
2. **Team member boundaries:** Each member owns their module — don't build features assigned to others
   - Aditya: LLM integration, prompts, CLI framework
   - Affan: Nmap, Event Logs, scanning commands
   - Suraj: Reports, CVE lookup
   - Sneha: OWASP/MITRE mappers, tests, docs
3. **Git workflow:** Work on personal branches (aditya, affan, suraj, sneha), merge to main only in Week 4
4. **API keys:** Never commit actual `.env` — only `.env.template`
5. **Nmap requirement:** Nmap must be installed separately on Windows (`C:\Program Files (x86)\Nmap\nmap.exe`)
6. **LLM fallback:** `prompt_engine.py` tries multiple Gemini models in order before failing
7. **Human-in-the-loop:** All scan/command execution should require user approval (planned for Week 3)
8. **Cross-platform:** All code must work on both Windows and Linux

---

## 11. Known Limitations

- Nmap must be installed separately on Windows
- Scanning requires network connectivity
- Only Gemini LLM currently integrated (OpenAI/Claude/Ollama pending)
- No Windows Event Log support yet (Week 3)
- No DOCX/PDF report generation yet (Week 3)
- No OWASP/MITRE mapping yet (Week 3)
- No pytest test suite yet (Week 3)
- README is minimal (needs full documentation)

---

## 12. Next Steps Priority

1. **Complete Week 2 (Days 10-14):** Prompt refinement, Ollama support, LLM switcher, team demo
2. **Start Week 3 (Days 15-21):** Windows Event Logs, remediation prompts, beginner mode, DOCX/PDF/MD reports
3. **Week 4 (Days 22-30):** Integration, polish, demo rehearsal, merge to main

**Current status: On schedule** — Week 1 complete, Week 2 through Day 11 complete.
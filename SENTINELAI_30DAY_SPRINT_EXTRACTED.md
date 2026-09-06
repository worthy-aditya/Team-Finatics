

SentinelAI CLI
30-Day Sprint Plan — Team Finatics
CodeQuest 4.0  |  July 2026

Aditya Gupta  •  Affan Shaikh  •  Suraj Yadav  •  Sneha Das


30-Day Sprint Overview

Sprint Goal — Days 1 to 30
By end of Day 30, SentinelAI CLI must have a working foundation: the core CLI running on both Windows and Linux, Nmap scanning integrated, first LLM API connected and returning plain-English analysis, and the GitHub repository set up with all team members contributing on separate branches.

Week
Days
Focus
Milestone
Week 1
Days 1–7
Setup & Foundation
GitHub live, dev environments ready, CLI skeleton running
Week 2
Days 8–14
Nmap + LLM Integration
Nmap scans working + AI analysis returning plain-English output
Week 3
Days 15–21
Windows Event Logs + Prompts
Windows log ingestion working + prompt engineering refined
Week 4
Days 22–30
Integration & First Demo
All Week 1–3 features connected end-to-end, first demo run


Week 1 — Days 1 to 7 — Setup & Foundation

Goal: Every team member has a working dev environment, the GitHub repo is live with branch structure, and the CLI skeleton accepts and runs basic commands.

Aditya Gupta
Project Lead & AI/LLM Integration

Day
Task
Deliverable
Day 1
Create GitHub repo (Team-Finatics/sentinelai-cli), set up branch structure
Repo live, branches: main, dev, aditya, affan, suraj, sneha
Day 2
Set up local Python environment, install Click and Rich libraries
Virtual environment running, CLI entry point created
Day 3
Build CLI skeleton — main command group, help text, version flag
python sentinelai.py --help returns proper output
Day 4
Set up .env file structure for API key management using dotenv
.env template committed to repo (without actual keys)
Day 5
Research and select primary LLM (OpenAI GPT-4o vs Claude Sonnet)
Decision documented in GitHub Wiki
Day 6
Connect first LLM API — send a test prompt, confirm response received
LLM API call working and returning text
Day 7
Team sync — review everyone's Week 1 progress, fix blockers
Week 1 retrospective notes in GitHub Discussions

Affan Shaikh
Security Tools & Scanning Engine

Day
Task
Deliverable
Day 1
Clone repo, set up local Python environment, install dependencies
Dev environment running on Affan's machine
Day 2
Install Nmap on Windows and Linux, verify it runs from command line
Nmap --version confirmed working on both platforms
Day 3
Install python-nmap library, write a basic scan script for localhost
Script runs scan and prints raw output to terminal
Day 4
Research python-nmap output structure — understand hosts, ports, states
Notes/diagram of Nmap output JSON structure in GitHub Wiki
Day 5
Build Nmap wrapper function — takes target IP, returns raw scan dict
Function written and manually tested on localhost
Day 6
Test scan on local network — verify output captures open ports/services
Test results documented with screenshot
Day 7
Attend team sync, demo Nmap wrapper to team, fix any issues raised
Wrapper code merged to affan branch on GitHub

Suraj Yadav
Report Generation & CVE Integration

Day
Task
Deliverable
Day 1
Clone repo, set up Python environment, install python-docx and fpdf2
Dev environment confirmed working
Day 2
Research NVD API — understand endpoints, rate limits, response format
API research notes added to GitHub Wiki
Day 3
Write first NVD API call — query a known CVE ID and print result
CVE-2021-44228 (Log4Shell) details returned successfully
Day 4
Design report template structure — sections, headings, severity color coding
Template design sketch/outline in GitHub Wiki
Day 5
Build basic DOCX report skeleton using python-docx with static test data
Static .docx file generated and saved locally
Day 6
Build basic PDF report skeleton using fpdf2 with same static test data
Static .pdf file generated and saved locally
Day 7
Attend team sync, demo both report skeletons to team
Report skeleton code merged to suraj branch

Sneha Das
OWASP Mapping, Testing & Documentation

Day
Task
Deliverable
Day 1
Clone repo, set up Python environment, install pytest
Dev environment confirmed working
Day 2
Download and study OWASP Top 10 JSON data structure
OWASP data file added to repo under /data folder
Day 3
Download and study MITRE ATT&CK STIX JSON dataset
MITRE data file added to repo under /data folder
Day 4
Write OWASP mapping function — takes a keyword, returns Top 10 category
Function returns correct category for test inputs
Day 5
Write pytest test cases for OWASP mapping function
3+ test cases passing in pytest
Day 6
Set up GitHub README with project description, setup instructions
README.md live on GitHub main branch
Day 7
Attend team sync, demo OWASP mapper and tests to team
Code merged to sneha branch on GitHub

✅  Week 1 Done When: GitHub repo live, all 4 dev environments working, CLI skeleton running, Nmap wrapper built, report skeletons generated, OWASP mapper with tests passing, README published.


Week 2 — Days 8 to 14 — Nmap + LLM Integration

Goal: Nmap scan output is fed into the LLM and returns a plain-English analysis. The two biggest components — scanning and AI — are connected for the first time.

Aditya Gupta
Project Lead & AI/LLM Integration

Day
Task
Deliverable
Day 8
Design the prompt template for Nmap analysis — what to ask the LLM
Prompt template v1 written and documented
Day 9
Feed sample Nmap output into LLM using prompt template — test response quality
LLM returns plain-English analysis of scan results
Day 10
Refine prompt — add instruction to identify risks and suggest next steps
Improved response quality confirmed with 3 test scans
Day 11
Build prompt engineering module — reusable functions for different analysis types
prompt_engine.py module created in repo
Day 12
Add Ollama support — install locally, connect same prompt to local LLM
Local Llama 3 via Ollama returning analysis offline
Day 13
Build LLM switcher — user can choose OpenAI/Claude/Gemini/Ollama via flag
--llm openai / --llm ollama flag working in CLI
Day 14
Team sync — full demo of scan → LLM analysis pipeline to whole team
Pipeline demo recorded as GIF/video for future pitch

Affan Shaikh
Security Tools & Scanning Engine

Day
Task
Deliverable
Day 8
Integrate Nmap wrapper into the main CLI as a --scan command
sentinelai --scan <IP> runs and prints raw results
Day 9
Parse Nmap output into structured dict (host, ports, services, states)
Structured JSON output from any scan confirmed
Day 10
Pass structured Nmap output to Aditya's prompt module for LLM analysis
Nmap → LLM pipeline working end-to-end
Day 11
Test scan + analysis on 3 different target types (localhost, LAN IP, test domain)
3 test results documented with output samples
Day 12
Handle edge cases — offline target, no open ports, permission denied errors
Error messages are clean and user-friendly
Day 13
Research Windows Event Log API — understand winevt and pywin32 libraries
Research notes added to GitHub Wiki
Day 14
Team sync — demo scan command with full LLM analysis output
sentinelai --scan code merged to affan branch

Suraj Yadav
Report Generation & CVE Integration

Day
Task
Deliverable
Day 8
Build CVE lookup function — takes a CVE ID, returns severity + description
Function returns clean CVE data for any valid CVE ID
Day 9
Build CVE search by keyword — search NVD by product name or vulnerability type
Keyword search returning top 5 relevant CVEs
Day 10
Connect CVE lookup to Nmap output — auto-match services to known CVEs
Nmap service names triggering CVE lookups automatically
Day 11
Build dynamic DOCX report — takes analysis text + CVE data, fills template
Real scan data populating a formatted Word document
Day 12
Build dynamic PDF report — same data filling fpdf2 template
Real scan data populating a formatted PDF
Day 13
Add severity color coding to reports — Critical=red, High=orange, Medium=yellow
Color-coded severity visible in both DOCX and PDF
Day 14
Team sync — demo CVE lookup and dynamic reports to team
Report generation code merged to suraj branch

Sneha Das
OWASP Mapping, Testing & Documentation

Day
Task
Deliverable
Day 8
Build MITRE ATT&CK mapper — takes a threat keyword, returns technique + ID
Function returns T-number and technique name for test inputs
Day 9
Write pytest tests for MITRE mapper with 5+ test cases
All tests passing in pytest
Day 10
Combine OWASP + MITRE mappers into single framework_mapper.py module
One module handling both mapping types
Day 11
Write integration test — Nmap output → MITRE mapper → correct technique
End-to-end mapping test passing
Day 12
Document all functions with docstrings and usage examples
All functions in repo have proper docstrings
Day 13
Update GitHub README with installation steps and first usage example
README updated with pip install and first command
Day 14
Team sync — demo framework mapper working on real scan output
framework_mapper.py merged to sneha branch

✅  Week 2 Done When: sentinelai --scan <IP> runs, AI returns plain-English analysis, CVEs auto-looked up, DOCX/PDF reports generating with real data, MITRE + OWASP mapping working.


Week 3 — Days 15 to 21 — Windows Event Logs + Prompt Refinement

Goal: Windows Event Log ingestion is working and feeding into the same AI analysis pipeline. Prompt quality is polished enough for a real demo.

Aditya Gupta
Project Lead & AI/LLM Integration

Day
Task
Deliverable
Day 15
Design prompt template for Windows Event Log analysis
Event log prompt template v1 written
Day 16
Feed sample Event Log output into LLM — test analysis quality
LLM correctly identifies suspicious login events
Day 17
Add remediation prompt layer — ask LLM to suggest specific fix steps
LLM now returns both finding + remediation in one response
Day 18
Refine all prompts based on Week 2 output quality review
Prompt v2 for Nmap and Event Log analysis committed
Day 19
Add beginner mode prompt — simpler language, Security+ aligned explanations
--beginner flag switching to simplified explanation style
Day 20
Test all prompt types across OpenAI, Claude, and Ollama — compare quality
Comparison table of outputs documented in GitHub Wiki
Day 21
Team sync — full pipeline demo (scan + logs + AI + remediation) to team
Demo notes and any blockers logged in GitHub Issues

Affan Shaikh
Security Tools & Scanning Engine

Day
Task
Deliverable
Day 15
Set up pywin32 / winevt — read Windows Security Event Log in Python
Event log entries printing to terminal from Python
Day 16
Filter for security-critical Event IDs — 4624 (login), 4625 (failed login), 4720 (new user)
Filtered log reader returning only critical events
Day 17
Build Windows Event Log parser — structured dict output per event
Parsed events returning EventID, time, user, IP fields
Day 18
Integrate Event Log parser into CLI as --logs command
sentinelai --logs running and returning parsed events
Day 19
Pass parsed log output to Aditya's prompt module for LLM analysis
sentinelai --logs → AI analysis pipeline working
Day 20
Build human-in-the-loop approval — prompt user before running any scan/command
CLI asks 'Confirm scan on <target>? (y/n)' before executing
Day 21
Team sync — demo --logs command with AI analysis to team
--logs code merged to affan branch

Suraj Yadav
Report Generation & CVE Integration

Day
Task
Deliverable
Day 15
Add Event Log section to DOCX and PDF report templates
Reports now have dedicated Event Log findings section
Day 16
Add MITRE ATT&CK and OWASP section to reports — auto-filled from mapper
Reports show mapped techniques and OWASP categories
Day 17
Add remediation steps section to reports — pulled from LLM output
Reports include specific fix steps per finding
Day 18
Build Markdown report generator — same content in .md format
sentinelai --report md generating valid Markdown file
Day 19
Add report output flag to CLI — user specifies --report docx/pdf/md
All three report types selectable from one command
Day 20
Test full report generation with combined Nmap + Event Log data
Single report covering both scan and log findings
Day 21
Team sync — demo complete report generation to team
Report generation code merged to suraj branch

Sneha Das
OWASP Mapping, Testing & Documentation

Day
Task
Deliverable
Day 15
Write integration tests for the full Nmap → LLM → report pipeline
End-to-end pipeline test passing in pytest
Day 16
Write integration tests for Event Log → LLM → report pipeline
Log pipeline test passing in pytest
Day 17
Build remediation mapper — maps OWASP/MITRE finding to fix instructions
remediation_mapper.py returning fix steps for test inputs
Day 18
Write pytest tests for remediation mapper with 5+ cases
All remediation tests passing
Day 19
Cross-platform test — run all tests on Linux environment
All tests passing on both Windows and Linux confirmed
Day 20
Write user documentation — How to install, configure, and run first scan
USAGE.md added to repo with step-by-step guide
Day 21
Team sync — demo full test suite running, show zero failures
Test report shared in GitHub Discussions

✅  Week 3 Done When: sentinelai --scan and --logs both working with AI analysis, remediation steps in output, all three report formats generating, full test suite passing on Windows and Linux.


Week 4 — Days 22 to 30 — Integration, Polish & First Demo

Goal: Everything built in Weeks 1–3 is connected, polished, and working end-to-end. The team runs a complete demo and the code is merged into a clean main branch.

Aditya Gupta
Project Lead & AI/LLM Integration

Day
Task
Deliverable
Day 22
Code review — review all team branches, raise issues for bugs or inconsistencies
GitHub Issues created for all identified bugs
Day 23
Fix any LLM-related bugs found in review — prompt edge cases, API errors
LLM module bug-free and handling errors gracefully
Day 24
Polish CLI output — add colors, progress indicators, clean status messages
Terminal output looks professional using Rich library
Day 25
Write complete end-to-end test — full scan + logs + AI + report in one command
One-command pipeline test passing cleanly
Day 26
Prepare demo script — exact commands to run for the hackathon presentation
Demo script documented in GitHub Wiki
Day 27
Run full demo rehearsal with team — time it, identify any failures
Demo runs under 3 minutes with zero crashes
Day 28
Fix any last issues found in demo rehearsal
All demo blockers resolved
Day 29
Merge all branches into main — final code review before merge
Clean main branch with all features integrated
Day 30
Day 30 milestone review — all features checklist, final team sign-off
Day 30 milestone report committed to GitHub

Affan Shaikh
Security Tools & Scanning Engine

Day
Task
Deliverable
Day 22
Fix any Nmap/Event Log bugs found in code review
All scanning bugs resolved and retested
Day 23
Test Nmap scanning on 5 different targets — document all outputs
Test results and edge cases documented
Day 24
Test Windows Event Log parser on different Windows versions/configs
Log parser confirmed working on Windows 10 and 11
Day 25
Improve human-in-the-loop UX — cleaner prompts, better confirmation messages
Approval flow clean and intuitive in terminal
Day 26
Add Linux log support — basic /var/log/auth.log parsing for failed logins
sentinelai --logs working on Linux as well as Windows
Day 27
Rehearse demo — run scan + logs commands in live demo flow
Demo commands memorized and running smoothly
Day 28
Fix any last scanning/log issues from rehearsal
All scanning issues resolved
Day 29
Final PR from affan branch to main — clean code, no debug prints
Affan's code merged to main branch
Day 30
Final verification — all scanning features working on clean main branch
Sign-off on Day 30 milestone checklist

Suraj Yadav
Report Generation & CVE Integration

Day
Task
Deliverable
Day 22
Fix any report generation bugs found in code review
All report bugs resolved and retested
Day 23
Polish DOCX report design — better formatting, logo placeholder, cover page
DOCX report looks fully professional
Day 24
Polish PDF report design — consistent fonts, color coding, page numbers
PDF report matches DOCX quality
Day 25
Test CVE lookup with rate limiting — handle NVD API limits gracefully
CVE lookup handles API errors without crashing
Day 26
Add executive summary section to all reports — 3-line non-technical overview
Executive summary auto-generated at top of every report
Day 27
Rehearse demo — generate report live during demo flow, show final output
Report generation fits into demo timeline cleanly
Day 28
Fix any last report/CVE issues from rehearsal
All report issues resolved
Day 29
Final PR from suraj branch to main — clean report templates committed
Suraj's code merged to main branch
Day 30
Final verification — DOCX, PDF, MD all generating correctly from main
Sign-off on Day 30 milestone checklist

Sneha Das
OWASP Mapping, Testing & Documentation

Day
Task
Deliverable
Day 22
Fix any mapping/test bugs found in code review
All mapping bugs resolved
Day 23
Run full pytest suite on integrated codebase — fix any new failures
100% tests passing on integrated code
Day 24
Write GitHub Wiki — Architecture overview diagram, data flow explanation
Architecture page live on GitHub Wiki
Day 25
Write contributor guide — how future open-source contributors can add tools
CONTRIBUTING.md added to repo
Day 26
Final cross-platform test — complete pipeline on Windows AND Linux
Confirmed working on both OS with test logs
Day 27
Rehearse demo — explain OWASP/MITRE mappings in demo narrative
Mapping explanation rehearsed and timed
Day 28
Fix any last test/doc issues from rehearsal
All documentation complete and accurate
Day 29
Final PR from sneha branch to main — all tests and docs committed
Sneha's code merged to main branch
Day 30
Final test run on clean main branch — all 13 MVP features verified
Sign-off on Day 30 milestone checklist

✅  Day 30 Done When: All code merged to main, full pipeline demo runs under 3 minutes with zero crashes, 13 MVP features all verified, reports generating professionally, test suite 100% passing on Windows and Linux.


30-Day Summary — What Each Member Delivers

Member
Role
Day 30 Deliverable
Aditya Gupta
Project Lead & AI/LLM
CLI framework, LLM integration (OpenAI/Claude/Gemini/Ollama), prompt engineering, beginner mode, demo script
Affan Shaikh
Scanning Engine
Nmap integration, Windows Event Log parser, Linux auth.log parser, human-in-the-loop safety, CLI --scan and --logs commands
Suraj Yadav
Reports & CVE
DOCX/PDF/Markdown report generation, CVE NVD lookup, executive summary, severity color coding, complete report templates
Sneha Das
Mapping, Testing & Docs
OWASP Top 10 mapper, MITRE ATT&CK mapper, remediation mapper, full pytest suite, README/USAGE/CONTRIBUTING docs, cross-platform verification


SentinelAI CLI  —  Learn. Analyze. Secure.
Team Finatics  |  CodeQuest 4.0  |  July 2026
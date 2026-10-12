# Team Finatics — Day 1 to Day 44 Project Report

## 1. Project Summary

This project, SentinelAI, is a Python-based security analysis and reporting system designed to transform raw security data into actionable vulnerability intelligence. The system converts Nmap output and event logs into OWASP Top 10:2025 categories and MITRE ATT&CK mappings, adds AI-based explanation when available, and produces structured security reports in multiple formats.

The project was developed and validated using Python, JSON datasets, pytest testing, and optional Gemini AI analysis. It is intended for authorized, in-scope security review workflows and includes ethical-use and consent controls to prevent misuse.

## 2. Objective of the Work

The core objective was to build a workflow where a user can:

- input raw security findings from Nmap or event logs
- detect relevant indicators and attack patterns
- map them to OWASP and MITRE frameworks
- optionally enrich the findings with AI-generated explanation
- generate a final remediation-oriented report
- validate the project in a safe, permission-aware process

This was completed as a multi-stage engineering effort spanning milestones from Day 1 to Day 44.

## 3. What Was Built

### 3.1 Core Mapping Engine
The system includes the following major modules:

- `owasp_mapper.py` — maps keywords to OWASP Top 10:2025 categories
- `mitre_mapper.py` — maps keywords to MITRE ATT&CK techniques
- `framework_mapper.py` — combines OWASP and MITRE mapping in one interface
- `nmap_parser.py` — parses raw Nmap output and extracts attack indicators
- `event_log_parser.py` — parses event log content and infers likely attack patterns
- `remediation_mapper.py` — converts mapped findings into remediation steps
- `llm_analyzer.py` — adds AI-based security explanation using Gemini, with offline fallback
- `report_generator.py` — creates report output in text, JSON, or Markdown

### 3.2 Full Pipelines
The project includes end-to-end pipelines:

- `nmap_report_pipeline.py` — Nmap -> mapping -> explanation -> report
- `event_log_report_pipeline.py` — event log -> mapping -> explanation -> report

These pipelines represent the main operational flow of the project and are the basis for the final project output.

### 3.3 Safety and Workflow Controls
The project also includes authorized-scan guard logic:

- `consent_gate.py`
- `domain_verifier.py`
- `access_policy.py`
- `session_guard.py`
- `policy_guard.py`
- `validation_guard.py`
- `compliance_guard.py`

This allows the workflow to verify that the scan target is approved, in scope, and permissioned before proceeding with active security scanning.

## 4. Data Sources and Frameworks Used

The project uses the following data and standards:

### 4.1 OWASP Data
- `data/owasp_top10.json`
- OWASP Top 10:2025 standard

This dataset powers the risk classification mapping from security indicators to categories such as injection, broken access control, and misconfiguration.

### 4.2 MITRE Data
- `data/enterprise-attack.json`
- `data/mobile-attack.json`
- `data/ics-attack.json`

These attack matrices provide MITRE ATT&CK technique references used to label malicious patterns and tactics.

### 4.3 LLM Analysis
- Google Gemini API for natural-language explanation
- Deterministic rule-based fallback when the API key is unavailable

This allows the project to work even without network-based AI access, which was a critical milestone for offline validation.

### 4.4 Security Testing Stack
- `pytest` for automated validation
- End-to-end tests for both Nmap and event-log pipelines
- Regression coverage for mapping, remediation, and reporting features

## 5. How the System Works

The end-to-end process is as follows:

1. Input is collected from raw Nmap output or security event logs.
2. The parser extracts likely indicators such as suspicious ports, failed logins, or attack-related keywords.
3. The keywords are passed through `framework_mapper.py`.
4. OWASP and MITRE mappings are generated for each indicator.
5. AI analysis is optionally added using Gemini; otherwise, a fallback rule engine is used.
6. The findings are summarized and formatted into a report.
7. The generated output is returned as text, JSON, or Markdown.

This makes the system useful for both technical and management audiences.

## 6. Day-by-Day Milestone Summary

The repository records the following completed milestone checkpoints:

- Day 4: Report template and reporting design
- Day 15: Nmap-to-LLM-to-report pipeline validation
- Day 16: Event log-to-LLM-to-report pipeline validation
- Day 22: Code review and quality assessment
- Day 23: Full automated test run
- Day 26: Cross-platform validation and final functional check
- Day 27: Demo rehearsal and presentation readiness
- Day 29: Pull request merge and branch completion
- Day 30: Final sign-off and verification
- Day 44: Sprint completion and final milestone confirmation

These milestones show steady progress from initial concept and mapping logic to a tested, signed-off project.

## 7. Tools and Technologies Used

The work was completed using the following toolchain:

- Python 3
- VS Code
- PowerShell / terminal execution
- Git / GitHub-based branch management
- `venv` virtual environment
- `pip` for dependency management
- `pytest` for validation
- JSON datasets and structured data processing
- Gemini AI integration for explanatory analysis
- Manual verification and documentation records in Markdown

## 8. Validation and Evidence

The project includes explicit verification evidence in the repository:

- `Day30 final sign-off.md` confirms the repository was validated on `main`
- `pytest -v` reported passing results
- Day 15 integration tests passed
- Day 16 integration tests passed
- Cross-platform checks were confirmed working on both Windows and Linux environments
- Final sprint milestone documentation states the repository supports the required controlled workflow

This means the project was not only built, but also verified with evidence.

## 9. Final Outcome

By Day 44, the project had reached a working, documented, and tested state that supports:

- keyword-based OWASP mapping
- MITRE ATT&CK mapping
- Nmap and event-log parsing
- AI analysis with fallback
- remediation guidance
- multi-format reporting
- signed-off operational workflow for authorized use

The final state is a complete security intelligence pipeline designed to convert raw indicators into human-readable, security-relevant outputs.

## 10. Conclusion

This project represents a full-cycle security research and reporting workflow built in Python. It combines data mapping, natural-language AI explanation, reporting, and safety controls into one coherent system. The repository documents the work up to Day 44 and validates the output through actual tests and milestone sign-off documentation.

The project demonstrates how a practical cybersecurity utility can be built using structured security datasets, parser logic, model-based explanation, and formal verification processes.

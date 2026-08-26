# SentinelAI Architecture

## Purpose

SentinelAI converts security observations into consistent OWASP Top 10:2025
and MITRE ATT&CK mappings. It supports Nmap service output and security event
log text as input, then produces an analysis summary and a text, JSON, or
Markdown report.

## System Overview

```text
Nmap output --------------------> nmap_parser.py
                                      |
Event log text -----------------> event_log_parser.py
                                      |
                                      v
                              keyword extraction
                                      |
                                      v
                              framework_mapper.py
                              /                 \
                   owasp_mapper.py       mitre_mapper.py
                              \                 /
                               v               v
                              mapped findings
                                      |
                                      v
                              llm_analyzer.py
                         Gemini API or offline fallback
                                      |
                                      v
                              report_generator.py
                         text | JSON | Markdown
```

## Main Modules

| Module | Responsibility |
|---|---|
| `nmap_parser.py` | Parses open Nmap TCP/UDP service lines and extracts known indicators. |
| `event_log_parser.py` | Parses event-log entries and extracts security indicators. |
| `owasp_mapper.py` | Loads OWASP Top 10:2025 data and maps keywords to categories. |
| `mitre_mapper.py` | Loads Enterprise, Mobile, and ICS ATT&CK data and maps keywords to techniques. |
| `framework_mapper.py` | Provides the single `map_keyword()` entry point for both frameworks. |
| `llm_analyzer.py` | Generates Gemini-backed analysis when configured, with a deterministic offline fallback. |
| `report_generator.py` | Renders mapped findings and analysis as text, JSON, or Markdown. |
| `nmap_report_pipeline.py` | Orchestrates Nmap parsing, mapping, analysis, and reporting. |
| `event_log_report_pipeline.py` | Orchestrates the equivalent event-log workflow. |
| `remediation_mapper.py` | Adds actionable remediation guidance for mapped OWASP categories and MITRE techniques. |

## Data Flow

1. An input adapter parses raw Nmap output or event-log text.
2. The adapter extracts known security indicators in their original order and
   removes duplicates.
3. `framework_mapper.map_keyword()` maps each indicator to OWASP and MITRE.
4. `llm_analyzer.analyze_findings()` uses Gemini only when an API key is
   configured; otherwise it returns an offline rule-based summary.
5. `report_generator.generate_report()` serializes the result in the requested
   format.
6. The pipeline returns the keywords, findings, analysis, and rendered report
   so callers can inspect structured data as well as the final output.

## External Data and Configuration

- OWASP data is stored in `data/owasp_top10.json`.
- MITRE data is stored in the Enterprise, Mobile, and ICS JSON files under
  `data/`.
- `GEMINI_API_KEY` is optional and must be supplied through the environment.
- `GEMINI_MODEL` optionally overrides the configured Gemini model.
- No API key or scan target is stored in source control.

## Testing Boundary

Unit tests cover parsers, mapping behavior, remediation lookup, and report
formatting. Integration tests exercise the end-to-end pipelines with
`use_llm=False`, keeping normal test runs deterministic and network-independent.
Run the complete suite from the repository root with:

```bash
pytest -v
```

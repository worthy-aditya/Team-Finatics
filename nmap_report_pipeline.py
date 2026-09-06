"""
nmap_report_pipeline.py

Ties together the full pipeline required for Day 15:

    raw Nmap output
        -> nmap_parser (parse + extract keywords)
        -> framework_mapper (OWASP + MITRE lookup per keyword)
        -> llm_analyzer (analysis summary)
        -> report_generator (final formatted report)
"""

from nmap_parser import parse_nmap_output, extract_keywords
from framework_mapper import map_keyword
from llm_analyzer import analyze_findings
from report_generator import generate_report


def run_nmap_to_report(nmap_output, report_format="text", audience="general", use_llm=True):
    """
    Run the full Nmap -> mapping -> analysis -> report pipeline.

    Args:
        nmap_output (str): Raw Nmap scan output (as produced by `nmap -sV`).
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
            "keywords": list[str],       # extracted indicator keywords
            "findings": list[dict],      # per-keyword OWASP+MITRE mapping
            "analysis": str,             # generated analysis summary
            "report": str,               # final formatted report
        }

    Example:
        >>> output = "22/tcp open ssh OpenSSH 8.9p1 Ubuntu"
        >>> result = run_nmap_to_report(output, use_llm=False)
        >>> "ssh" in result["keywords"]
        True
    """
    services = parse_nmap_output(nmap_output)
    keywords = extract_keywords(services)

    findings = [map_keyword(kw) for kw in keywords]

    analysis = analyze_findings(findings, audience=audience, use_llm=use_llm)

    report = generate_report(findings, analysis, report_format=report_format)

    return {
        "keywords": keywords,
        "findings": findings,
        "analysis": analysis,
        "report": report,
    }


if __name__ == "__main__":
    sample_nmap_output = """
PORT     STATE SERVICE      VERSION
22/tcp   open  ssh          OpenSSH 8.9p1 Ubuntu
5985/tcp open  http         Microsoft HTTPAPI httpd 2.0 (PowerShell remoting)
"""
    result = run_nmap_to_report(sample_nmap_output, report_format="text")
    print(result["report"])


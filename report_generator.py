"""
report_generator.py

Formats mapped findings and their analysis summary into a final report,
in one of three output formats: plain text, JSON, or Markdown.
"""

import json
from datetime import datetime, timezone


def _generate_text_report(findings, analysis):
    """Build a plain-text report."""
    lines = [
        "=" * 60,
        "SENTINELAI SECURITY FINDINGS REPORT",
        "=" * 60,
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Total findings: {len(findings)}",
        "",
        "--- FINDINGS ---",
    ]
    for i, f in enumerate(findings, start=1):
        lines.append(f"\n[{i}] Keyword: {f.get('keyword')}")
        if f.get("owasp"):
            lines.append(f"    OWASP: {f['owasp']['rank']} - {f['owasp']['name']}")
        else:
            lines.append("    OWASP: No match")
        if f.get("mitre"):
            m = f["mitre"]
            lines.append(f"    MITRE: {m['id']} - {m['name']} [{m['domain']}]")
        else:
            lines.append("    MITRE: No match")

    lines.append("\n--- ANALYSIS ---")
    lines.append(analysis)
    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


def _generate_json_report(findings, analysis):
    """Build a JSON report as a string."""
    report = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "total_findings": len(findings),
        "findings": findings,
        "analysis": analysis,
    }
    return json.dumps(report, indent=2)


def _generate_markdown_report(findings, analysis):
    """Build a Markdown report."""
    lines = [
        "# SentinelAI Security Findings Report",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        f"**Total findings:** {len(findings)}",
        "",
        "## Findings",
        "",
        "| # | Keyword | OWASP | MITRE |",
        "|---|---|---|---|",
    ]
    for i, f in enumerate(findings, start=1):
        owasp_str = f"{f['owasp']['rank']} - {f['owasp']['name']}" if f.get("owasp") else "No match"
        mitre_str = f"{f['mitre']['id']} - {f['mitre']['name']} [{f['mitre']['domain']}]" if f.get("mitre") else "No match"
        lines.append(f"| {i} | {f.get('keyword')} | {owasp_str} | {mitre_str} |")

    lines.append("")
    lines.append("## Analysis")
    lines.append("")
    lines.append(analysis)
    return "\n".join(lines)


_FORMAT_GENERATORS = {
    "text": _generate_text_report,
    "json": _generate_json_report,
    "markdown": _generate_markdown_report,
}


def generate_report(findings, analysis, report_format="text"):
    """
    Generate a formatted report from mapped findings and an analysis summary.

    Args:
        findings (list[dict]): Mapped findings, each shaped like
            {"keyword": str, "owasp": dict|None, "mitre": dict|None}.
        analysis (str): The analysis summary text (e.g. from
            llm_analyzer.analyze_findings()).
        report_format (str): One of "text", "json", or "markdown".
            Defaults to "text".

    Returns:
        str: The formatted report.

    Raises:
        ValueError: If report_format is not one of the supported formats.

    Example:
        >>> findings = [{"keyword": "phishing", "owasp": None,
        ...     "mitre": {"id": "T1566", "name": "Phishing", "domain": "enterprise"}}]
        >>> report = generate_report(findings, "Sample analysis.", "json")
        >>> "T1566" in report
        True
    """
    if report_format not in _FORMAT_GENERATORS:
        raise ValueError(
            f"Unsupported report_format '{report_format}'. "
            f"Must be one of: {list(_FORMAT_GENERATORS.keys())}"
        )
    return _FORMAT_GENERATORS[report_format](findings, analysis)


if __name__ == "__main__":
    sample_findings = [
        {
            "keyword": "phishing",
            "owasp": None,
            "mitre": {"id": "T1566", "name": "Phishing", "domain": "enterprise"},
        },
    ]
    sample_analysis = "Sample analysis text."
    for fmt in ["text", "json", "markdown"]:
        print(f"\n--- {fmt.upper()} ---")
        print(generate_report(sample_findings, sample_analysis, fmt))
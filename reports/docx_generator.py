"""DOCX rendering helpers for active dynamic-scan findings."""

from dataclasses import asdict, is_dataclass
from typing import Any, Iterable

from docx import Document
from docx.shared import RGBColor


def _finding_value(finding: Any, name: str, default: str = "") -> str:
    if is_dataclass(finding):
        return str(getattr(finding, name, default) or default)
    if isinstance(finding, dict):
        return str(finding.get(name, default) or default)
    return str(getattr(finding, name, default) or default)


def add_active_findings_section(
    doc: Document, active_findings: Iterable[Any]
) -> None:
    """Render the dedicated confirmed active-testing section in a DOCX."""
    findings = list(active_findings)
    doc.add_heading("Active Testing Findings", level=1)

    notice = doc.add_paragraph()
    notice.add_run(
        "Notice: The following vulnerabilities were identified via active "
        "dynamic testing. These represent confirmed/validated findings "
        "against the authorized target."
    ).italic = True

    if not findings:
        doc.add_paragraph("No active testing vulnerabilities were detected.")
        return

    for finding in findings:
        heading = doc.add_heading(level=2)
        severity = _finding_value(finding, "severity", "Unknown")
        title = _finding_value(finding, "title", "Untitled finding")
        run = heading.add_run(f"[{severity.upper()}] {title}")
        if severity.lower() in {"high", "critical"}:
            run.font.color.rgb = RGBColor(200, 0, 0)

        table = doc.add_table(rows=5, cols=2)
        table.style = "Table Grid"
        details = [
            ("Target Endpoint:", _finding_value(finding, "target_url", "N/A")),
            ("Confidence Level:", _finding_value(finding, "confidence", "N/A")),
            ("Associated CVE:", _finding_value(finding, "cve_id", "N/A")),
            ("Description:", _finding_value(finding, "description")),
            ("Remediation:", _finding_value(finding, "remediation", "N/A")),
        ]
        for row, (label, value) in zip(table.rows, details):
            row.cells[0].text = label
            row.cells[1].text = value

        for evidence_name, label in (
            ("evidence_request", "Evidence (HTTP Request):"),
            ("evidence_response", "Evidence (HTTP Response):"),
        ):
            evidence = _finding_value(finding, evidence_name)
            if evidence:
                doc.add_heading(label, level=3)
                code = doc.add_paragraph()
                code.add_run(evidence).font.name = "Courier New"

        doc.add_paragraph()
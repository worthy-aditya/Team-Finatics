"""PDF rendering helpers for active dynamic-scan findings."""

from typing import Any, Iterable

from fpdf import FPDF
from fpdf.enums import XPos, YPos


def _finding_value(finding: Any, name: str, default: str = "") -> str:
    if isinstance(finding, dict):
        return str(finding.get(name, default) or default)
    return str(getattr(finding, name, default) or default)


class SentinelReportPDF(FPDF):
    """PDF document with a dedicated active-testing findings section."""

    def add_active_findings_section(self, active_findings: Iterable[Any]) -> None:
        findings = list(active_findings)
        self.add_page()
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "Active Testing Findings", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

        self.set_font("Helvetica", "I", 10)
        self.multi_cell(
            0,
            5,
            "The following findings represent confirmed issues discovered "
            "through active scan verification.",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.ln(5)

        if not findings:
            self.set_font("Helvetica", "", 10)
            self.multi_cell(
                0,
                5,
                "No active testing vulnerabilities were detected.",
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
            return

        for finding in findings:
            severity = _finding_value(finding, "severity", "Unknown")
            self.set_font("Helvetica", "B", 12)
            if severity.lower() in {"high", "critical"}:
                self.set_text_color(200, 0, 0)
            self.cell(
                0,
                8,
                f"[{severity.upper()}] {_finding_value(finding, 'title', 'Untitled finding')}",
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
            self.set_text_color(0, 0, 0)

            self.set_font("Helvetica", "", 10)
            self.multi_cell(
                0,
                5,
                f"Target: {_finding_value(finding, 'target_url', 'N/A')}",
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
            self.multi_cell(
                0,
                5,
                f"Confidence: {_finding_value(finding, 'confidence', 'N/A')}",
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
            self.multi_cell(
                0,
                5,
                f"Description: {_finding_value(finding, 'description')}",
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
            cve_id = _finding_value(finding, "cve_id")
            if cve_id:
                self.multi_cell(
                    0, 5, f"CVE: {cve_id}", new_x=XPos.LMARGIN, new_y=YPos.NEXT
                )
            remediation = _finding_value(finding, "remediation")
            if remediation:
                self.multi_cell(
                    0,
                    5,
                    f"Remediation: {remediation}",
                    new_x=XPos.LMARGIN,
                    new_y=YPos.NEXT,
                )
            for evidence_name, label in (
                ("evidence_request", "HTTP Request"),
                ("evidence_response", "HTTP Response"),
            ):
                evidence = _finding_value(finding, evidence_name)
                if evidence:
                    self.set_font("Courier", "", 8)
                    self.multi_cell(
                        0,
                        4,
                        f"{label}: {evidence}",
                        new_x=XPos.LMARGIN,
                        new_y=YPos.NEXT,
                    )
                    self.set_font("Helvetica", "", 10)
            self.ln(4)
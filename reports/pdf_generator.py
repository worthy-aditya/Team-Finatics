"""PDF rendering helpers for active dynamic-scan findings."""

from typing import Any, Iterable

from fpdf import FPDF
from fpdf.enums import XPos, YPos


def _finding_value(finding: Any, name: str, default: str = "") -> str:
    if isinstance(finding, dict):
        return str(finding.get(name, default) or default)
    return str(getattr(finding, name, default) or default)


def add_finding_card_pdf(
    pdf: FPDF, finding: Any, finding_type: str = "PASSIVE"
) -> None:
    """Render a finding with distinct active and passive visual treatment."""
    active = finding_type.upper() == "ACTIVE"
    pdf.set_fill_color(*( (217, 83, 79) if active else (252, 228, 178) ))
    pdf.set_text_color(255, 255, 255) if active else pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "B", 10)
    tag = "[CONFIRMED EXPLOITABLE]" if active else "[POTENTIAL]"
    pdf.multi_cell(
        0, 8, f" {tag} {_finding_value(finding, 'title', 'Untitled finding')}",
        border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    target = _finding_value(finding, "target", _finding_value(finding, "target_url", "N/A"))
    pdf.multi_cell(
        0, 5,
        f"Severity: {_finding_value(finding, 'severity', 'Medium')}\n"
        f"Target: {target}\nDescription: {_finding_value(finding, 'description')}",
        border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )
    pdf.ln(4)


class SentinelReportPDF(FPDF):
    """PDF document with a dedicated active-testing findings section."""

    def add_finding_card_pdf(
        self, finding: Any, finding_type: str = "PASSIVE"
    ) -> None:
        """Render a visually distinct active or passive finding card."""
        add_finding_card_pdf(self, finding, finding_type)

    def header(self) -> None:
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(100, 100, 100)
            self.cell(0, 5, "SentinelAI CLI Security Report", align="R")
            self.set_text_color(0, 0, 0)
            self.ln(6)

    def footer(self) -> None:
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, f"Page {self.page_no()}", align="C")
        self.set_text_color(0, 0, 0)

    def add_active_findings_section(self, active_findings: Iterable[Any]) -> None:
        findings = list(active_findings)
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
            self.add_finding_card_pdf(finding, finding_type="ACTIVE")
            self.set_font("Helvetica", "", 10)
            self.multi_cell(
                0,
                5,
                f"Confidence: {_finding_value(finding, 'confidence', 'N/A')}",
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

    def add_authorization_record_pdf(self, auth_record: Any) -> None:
        """Append the authorization and ownership verification record."""
        self.add_page()
        self.set_font("Helvetica", "B", 14)
        self.cell(
            0,
            10,
            "Appendix: Authorization & Verification Record",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.ln(2)
        self.set_font("Helvetica", "I", 9)
        self.multi_cell(
            0,
            5,
            "Audit Trail Disclaimer: Immutable record of ownership verification "
            "and user consent.",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.ln(5)

        details = [
            ("Target Domain:", _finding_value(auth_record, "target_domain", "N/A")),
            ("Attestation User:", _finding_value(auth_record, "attestation_user", "N/A")),
            ("Timestamp:", _finding_value(auth_record, "attestation_timestamp", "N/A")),
            ("Verification Method:", _finding_value(auth_record, "verification_method", "N/A")),
            ("Verification Status:", _finding_value(auth_record, "verification_status", "N/A")),
            ("Token Used:", _finding_value(auth_record, "token_used", "N/A")),
        ]
        for label, value in details:
            self.set_font("Helvetica", "B", 10)
            self.cell(50, 7, label, border=1)
            self.set_font("Helvetica", "", 10)
            if label == "Verification Status:":
                self.set_text_color(0, 150, 0 if value.upper() == "VERIFIED" else 0)
                if value.upper() != "VERIFIED":
                    self.set_text_color(200, 0, 0)
            self.cell(130, 7, value, border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.set_text_color(0, 0, 0)
        self.ln(5)
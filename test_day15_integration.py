"""
test_day15_integration.py

Day 15: End-to-end integration test for the full pipeline:
Nmap output -> keyword extraction -> OWASP/MITRE mapping ->
analysis (LLM stand-in) -> formatted report.
"""

from nmap_report_pipeline import run_nmap_to_report

SAMPLE_NMAP_OUTPUT = """
PORT     STATE SERVICE      VERSION
22/tcp   open  ssh          OpenSSH 8.9p1 Ubuntu
5985/tcp open  http         Microsoft HTTPAPI httpd 2.0 (PowerShell remoting)
"""


def test_pipeline_extracts_keywords():
    result = run_nmap_to_report(SAMPLE_NMAP_OUTPUT)
    assert "ssh" in result["keywords"]
    assert "powershell" in result["keywords"]


def test_pipeline_produces_findings_for_each_keyword():
    result = run_nmap_to_report(SAMPLE_NMAP_OUTPUT)
    assert len(result["findings"]) == len(result["keywords"])
    for finding in result["findings"]:
        assert "keyword" in finding
        assert "owasp" in finding
        assert "mitre" in finding


def test_pipeline_generates_non_empty_analysis():
    result = run_nmap_to_report(SAMPLE_NMAP_OUTPUT)
    assert isinstance(result["analysis"], str)
    assert len(result["analysis"]) > 0
    assert "finding" in result["analysis"].lower()


def test_pipeline_text_report_contains_expected_content():
    result = run_nmap_to_report(SAMPLE_NMAP_OUTPUT, report_format="text")
    report = result["report"]
    assert "SENTINELAI SECURITY FINDINGS REPORT" in report
    assert "ssh" in report.lower()
    assert "ANALYSIS" in report


def test_pipeline_json_report_is_valid_and_complete():
    import json
    result = run_nmap_to_report(SAMPLE_NMAP_OUTPUT, report_format="json")
    parsed = json.loads(result["report"])
    assert parsed["total_findings"] == len(result["findings"])
    assert "analysis" in parsed


def test_pipeline_markdown_report_has_table():
    result = run_nmap_to_report(SAMPLE_NMAP_OUTPUT, report_format="markdown")
    report = result["report"]
    assert "| # | Keyword | OWASP | MITRE |" in report


def test_pipeline_handles_benign_scan_with_no_indicators():
    benign_output = """
PORT     STATE SERVICE      VERSION
80/tcp   open  http         Apache httpd 2.4.41
"""
    result = run_nmap_to_report(benign_output)
    assert result["keywords"] == []
    assert result["findings"] == []
    assert "no findings" in result["analysis"].lower()
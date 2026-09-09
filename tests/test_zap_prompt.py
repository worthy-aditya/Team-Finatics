"""Day 35 unit tests for the ZAP active-scan prompt template (offline).

Day 35 deliverable: prompt template v1 drafted, DISTINCT from the existing
Nmap (Day 9/10) and Windows Event Log (Day 15) templates. These tests lock in
the template contract: five fixed sections, ZAP-specific fields, authorized
(consent + domain) framing, schema validation with fail-fast errors, and that
the sample fixture (day35_sample_zap_findings.json) satisfies the builder.
No LLM / network required - the prompt-vs-LLM quality check is Day 36.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sentinelai.prompt_engine import (
    DEFAULT_ZAP_ANALYSIS_OUTPUT_FILE,
    DEFAULT_ZAP_INPUT_FILE,
    EVENT_LOG_ANALYSIS_PROMPT,
    NMAP_ANALYSIS_PROMPT,
    PromptMode,
    ZAP_ANALYSIS_PROMPT,
    build_zap_prompt,
)

SAMPLE = ROOT / "day35_sample_zap_findings.json"


def _sample():
    return json.loads(SAMPLE.read_text(encoding="utf-8"))


def test_template_v1_exists_and_is_distinct():
    assert ZAP_ANALYSIS_PROMPT.strip()
    assert ZAP_ANALYSIS_PROMPT != NMAP_ANALYSIS_PROMPT
    assert ZAP_ANALYSIS_PROMPT != EVENT_LOG_ANALYSIS_PROMPT


def test_template_has_five_fixed_sections():
    for heading in (
        "## 1. Plain-English Summary",
        "## 2. Findings (ranked by risk)",
        "## 3. True-Positive Assessment",
        "## 4. Recommended Next Steps",
        "## 5. Confidence & Limitations",
    ):
        assert heading in ZAP_ANALYSIS_PROMPT, heading


def test_template_uses_zap_placeholder_only():
    assert "{zap_findings}" in ZAP_ANALYSIS_PROMPT
    assert "{scan_data}" not in ZAP_ANALYSIS_PROMPT
    assert "{event_log_data}" not in ZAP_ANALYSIS_PROMPT


def test_template_carries_zap_specific_vocabulary():
    for needle in (
        "OWASP",
        "plugin",
        "confidence",
        "True-Positive Assessment",
        "CWE",
        "web-application",
    ):
        assert needle.lower() in ZAP_ANALYSIS_PROMPT.lower(), needle


def test_template_encodes_authorized_context():
    # The Day 31-34 tie-in: the prompt states the two-layer gate ran first.
    low = ZAP_ANALYSIS_PROMPT.lower()
    assert "authorized" in low
    assert "attestation" in low
    assert "sentinelai-verify.txt" in low
    assert "defensive" in low


def test_builder_formats_sample_fixture():
    prompt = build_zap_prompt(_sample())
    assert "SQL Injection" in prompt
    assert '"plugin_id":40018' in prompt  # compact JSON payload, not indented
    assert '"source":"zap-active-scan"' in prompt
    assert '"alerts":[' in prompt
    # the LLM instruction template itself stays intact
    assert "ZAP plugin <plugin_id>" in prompt


def test_builder_rejects_non_dict():
    for bad in ("nope", ["list"], None, 42):
        try:
            build_zap_prompt(bad)
        except ValueError as exc:
            assert "'alerts'" in str(exc)
            continue
        raise AssertionError(f"expected ValueError for {bad!r}")


def test_builder_rejects_missing_alerts():
    try:
        build_zap_prompt({"source": "zap-active-scan", "count": 0})
    except ValueError as exc:
        assert "'alerts'" in str(exc)
        assert "day35_sample_zap_findings" in str(exc)
        return
    raise AssertionError("missing 'alerts' must raise ValueError")


def test_builder_rejects_event_log_style_schema():
    # Event-log-shaped input must fail with the ZAP-specific message, never
    # silently prompt with the wrong payload (Day 23 fail-fast convention).
    try:
        build_zap_prompt({"events": [{"event_id": 4625}]})
    except ValueError as exc:
        assert "alerts" in str(exc)
        return
    raise AssertionError("event-log schema should not pass the ZAP builder")


def test_builder_empty_alerts_is_valid_clean_scan():
    clean = {"source": "zap-active-scan", "target": "x", "alerts": []}
    prompt = build_zap_prompt(clean)
    assert "came back clean" in prompt


def test_builder_rejects_unbuilt_modes():
    for mode in (PromptMode.BEGINNER, PromptMode.REMEDIATION):
        try:
            build_zap_prompt(_sample(), mode=mode)
        except ValueError as exc:
            assert "not built yet" in str(exc)
            continue
        raise AssertionError(f"mode {mode} should raise ValueError")


def test_default_artifact_constants():
    assert str(DEFAULT_ZAP_INPUT_FILE) == "zap_findings.json"
    assert str(DEFAULT_ZAP_ANALYSIS_OUTPUT_FILE) == "day36_analysis_zap.md"


def test_sample_fixture_matches_documented_contract():
    data = _sample()
    assert data["source"] == "zap-active-scan"
    assert isinstance(data["alerts"], list) and data["alerts"]
    assert data["count"] == len(data["alerts"])
    required = {
        "plugin_id", "name", "risk", "confidence", "cwe_id", "url",
        "method", "param", "attack", "evidence", "description", "solution",
        "reference", "tags",
    }
    for alert in data["alerts"]:
        assert required <= set(alert), required - set(alert)
    assert data["authorized"]["domain_verified"] is True


def _main():
    # Windows pipe captures default to cp1252; keep direct runs encoding-safe.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    failures = 0
    for fn in fns:
        try:
            fn()
            print(f"  PASS  {fn.__name__}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"  FAIL  {fn.__name__}: {exc}")
    print(f"ALL {len(fns) - failures}/{len(fns)} zap-prompt TESTS PASSED (offline)")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    _main()
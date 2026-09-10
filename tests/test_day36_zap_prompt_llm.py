"""Day 36 harness - test the Day 35 ZAP prompt against mock ZAP-style findings.

Day 36 deliverable: "LLM returns plain-English explanation of a mock finding."

Two ways to run (Day 16 harness conventions):

  Offline (no network, mocked provider call - proves template + pipeline + the
  programmatic quality checks):
      python tests/test_day36_zap_prompt_llm.py --self-test

  Live (real LLM via gemini|ollama over the Day 35 mock findings; resume-safe
  artifact day36_analysis_zap[.suffix].md):
      python tests/test_day36_zap_prompt_llm.py --live --provider gemini

Quality checks (same philosophy as the Day 16 event-log harness - ground truth
lives only here, never in the prompt):
  - exactly the Day 35 five-section Markdown contract
  - every input alert is explained (plain-English "Why it matters")
  - no-fabrication guard: only plugin IDs present in the input may be cited
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sentinelai.prompt_engine import (  # noqa: E402
    DEFAULT_ZAP_ANALYSIS_OUTPUT_FILE,
    ScanAnalysisResult,
    analyze_zap_findings_data,
    load_zap_findings,
)

SAMPLE = ROOT / "day35_sample_zap_findings.json"
SECTIONS = (
    "## 1. Plain-English Summary",
    "## 2. Findings (ranked by risk)",
    "## 3. True-Positive Assessment",
    "## 4. Recommended Next Steps",
    "## 5. Confidence & Limitations",
)


def validate_zap_analysis(analysis: str, findings: dict) -> list:
    """Programmatic quality checks; returns a list of human-readable failures."""
    failures = []
    # 1. The five-section contract
    for section in SECTIONS:
        if section not in analysis:
            failures.append(f"missing section heading: {section}")

    alerts = findings.get("alerts", [])
    # 2. Every input alert is explained in plain English
    for alert in alerts:
        if alert["name"] not in analysis:
            failures.append(f"alert not explained: {alert['name']}")

    # 3. No-fabrication guard: only input plugin IDs may be cited
    allowed = {str(a["plugin_id"]) for a in alerts}
    cited = set(re.findall(r"plugin[ _-]?id[ <>:]*([0-9]{3,6})", analysis, re.I))
    cited |= set(re.findall(r"plugin ([0-9]{3,6})", analysis, re.I))
    fabricated = cited - allowed
    if fabricated:
        failures.append(f"fabricated plugin ID(s) cited: {sorted(fabricated)}")

    # 4. Findings section actually ranks findings (evidence-based structure)
    if alerts and not re.search(r"Finding #1 -", analysis):
        failures.append("no ranked finding (#1) in section 2")

    # 5. Plain-English requirement: 'Why it matters' explanations present
    if alerts and analysis.count("Why it matters") < 1:
        failures.append("no plain-English 'Why it matters' explanation present")
    return failures


# --- offline self-test: mock the provider call, prove pipeline + checks -----


def _fake_gemini(prompt: str, **kwargs):
    """Deterministic mock 'LLM' answer over the Day 35 fixture findings.

    Follows the template contract using ONLY the input data (no fabrication) -
    the same five sections a real model should produce.
    """
    findings = json.loads(re.search(r"(\{.*\})", prompt, re.S).group(1))
    alerts = findings["alerts"]
    lines = ["## 1. Plain-English Summary", "", "Mock analysis.", ""]
    lines += ["## 2. Findings (ranked by risk)", ""]
    for n, a in enumerate(alerts, 1):
        lines += [
            f"- **Finding #{n} - {a['name']} (ZAP plugin {a['plugin_id']})**",
            f"  - Severity: {a['risk']}, Confidence: {a['confidence']}",
            f"  - Why it matters: {a['description']}",
        ]
    lines += ["", "## 3. True-Positive Assessment", "Mock assessment.", ""]
    lines += ["## 4. Recommended Next Steps", "Mock steps.", ""]
    lines += ["## 5. Confidence & Limitations", "Mock limitations.", ""]
    return "mock-model", "\n".join(lines), {}


def test_offline_self_test() -> None:
    findings = load_zap_findings(SAMPLE)
    real = analyze_zap_findings_data.__globals__["_call_gemini"]
    try:
        # Inject the mock provider call (offline: no network, no key).
        analyze_zap_findings_data.__globals__["_call_gemini"] = _fake_gemini
        result = analyze_zap_findings_data(findings)
    finally:
        analyze_zap_findings_data.__globals__["_call_gemini"] = real

    assert isinstance(result, ScanAnalysisResult)
    assert result.provider.value == "gemini"  # routed through the pipeline
    assert result.model == "mock-model"
    failures = validate_zap_analysis(result.analysis, findings)
    assert not failures, failures
    print(f"  offline self-test OK ({len(findings['alerts'])} mock alerts validated)")


def _main() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="offline mocked run")
    parser.add_argument("--live", action="store_true", help="real LLM run")
    parser.add_argument("--provider", default="gemini", choices=["gemini", "ollama"])
    parser.add_argument("--force", action="store_true", help="rerun if artifact exists")
    parser.add_argument("--suffix", default="", help="artifact filename suffix")
    args = parser.parse_args()

    if not (args.self_test or args.live):
        args.self_test = True

    exit_code = 0

    if args.self_test:
        try:
            test_offline_self_test()
        except AssertionError as exc:
            print(f"  offline self-test FAILED: {exc}")
            exit_code = 1

    if args.live:
        from sentinelai.prompt_engine import resolve_provider

        findings = load_zap_findings(SAMPLE)
        suffix = f".{args.suffix}" if args.suffix else ""
        artifact = Path(str(DEFAULT_ZAP_ANALYSIS_OUTPUT_FILE).replace(
            ".md", f"{suffix}.md"))
        if artifact.exists() and not args.force:
            print(f"  artifact exists: {artifact} (use --force to rerun)")
        else:
            provider = resolve_provider(args.provider)
            print(f"  live run: {len(findings['alerts'])} mock alerts via "
                  f"{provider.value} (free providers can take 1-2 minutes)...")
            result = analyze_zap_findings_data(findings, provider=provider)
            artifact.write_text(
                f"# Day 36 ZAP Active-Scan LLM Analysis\n\n"
                f"Provider: {result.provider.value} | Model: `{result.model}`\n\n"
                f"{result.analysis}\n",
                encoding="utf-8",
            )
            print(f"  saved: {artifact} ({len(result.analysis)} chars via {result.model})")
        failures = validate_zap_analysis(artifact.read_text(encoding="utf-8"), findings)
        if failures:
            print("  LIVE QUALITY CHECK FAILED:")
            for failure in failures:
                print(f"    - {failure}")
            exit_code = 1
        else:
            print("  live quality checks PASSED (5 sections, alerts explained, "
                  "no fabricated plugin IDs)")

    print("Day 36 ZAP PROMPT TEST: " + ("PASSED" if exit_code == 0 else "FAILED"))
    raise SystemExit(exit_code)


if __name__ == "__main__":
    _main()
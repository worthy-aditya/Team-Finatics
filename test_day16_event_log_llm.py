"""Day 16 test wrapper: validate the LLM on sample Windows Event Log data.

Day 15 delivered the EVENT_LOG_ANALYSIS_PROMPT; Day 16 proves it works across
diverse scenarios and checks the model does NOT hallucinate.

Scenarios (each a realistic Security event log JSON):
    1. benign      - routine interactive/batch logons only; model must NOT
                     invent an attack or a Critical finding
    2. bruteforce  - overnight RDP brute force from one IP, account lockout,
                     then a successful 3 AM remote logon + explicit credentials
    3. incident    - (reuses day15_sample_events.json) audit log cleared +
                     backdoor account created + privilege group add

Checks performed per scenario (on the model's Markdown output):
    - 5/5 required section headers present
    - No-hallucination: every standalone 4-digit number must be a known input
      Event ID or the current year (catches invented event IDs)
    - Risk posture: highest severity mentioned vs the scenario ground truth
      (over/under-stating by 2+ levels is flagged)

Run:
    python test_day16_event_log_llm.py                     # ollama (local)
    python test_day16_event_log_llm.py --provider gemini   # cloud spot-check
    python test_day16_event_log_llm.py --self-test         # offline checks only
    python test_day16_event_log_llm.py --force             # re-run everything
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sentinelai.prompt_engine import (
    LLMProvider,
    analyze_event_log_file,
    list_ollama_models,
)

REQUIRED_SECTIONS = [
    "## 1. Plain-English Summary",
    "## 2. Security Events (ranked by risk)",
    "## 3. What These Events Suggest",
    "## 4. Recommended Next Steps",
    "## 5. Confidence & Limitations",
]

# Higher = more severe. Used to detect over/under-stated risk posture.
SEVERITY_LEVELS = {"info": 1, "low": 2, "medium": 3, "high": 4, "critical": 5}

# (name, input_json, output_md, expected_max_severity, note)
# Ground truth lives HERE, never in the JSON the model sees (that would leak
# the answer and defeat the point of an honesty test).
SCENARIOS = [
    {
        "name": "benign",
        "json": "day16_scenario_benign.json",
        "md": "day16_analysis_benign.md",
        "expected_max": "low",
        "note": "Routine logons only - model must NOT invent an attack",
    },
    {
        "name": "bruteforce",
        "json": "day16_scenario_bruteforce.json",
        "md": "day16_analysis_bruteforce.md",
        "expected_max": "high",
        "note": "Overnight RDP brute force + 3 AM remote logon with explicit creds",
    },
    {
        "name": "incident",
        "json": "day15_sample_events.json",
        "md": "day16_analysis_incident.md",
        "expected_max": "critical",
        "note": "Audit log cleared + backdoor account created (Day 15 sample)",
    },
]

CURRENT_YEAR = 2026
def missing_sections(text: str):
    """Return the required section headers absent from the analysis."""
    return [h for h in REQUIRED_SECTIONS if h not in text]


def four_digit_numbers(text: str):
    """All standalone 4-digit integers in the text (event IDs, years, etc.)."""
    return sorted({int(m) for m in re.findall(r"\b\d{4}\b", text)})


def hallucinated_event_ids(text: str, known_event_ids):
    """4-digit numbers NOT known input Event IDs (or the current year).

    Scans only the ANALYSIS body (sections 1-3, up to "Recommended Next
    Steps") and skips NEGATED references like "no 4625 events" or "not 1102"
    (the model correctly noting an Event ID's ABSENCE is not a fabrication).
    Advice in Next Steps may legitimately suggest checking OTHER Event IDs
    (e.g. "look for 4720/4728 account changes"), so those are excluded too.
    """
    body = text.split("## 4. Recommended Next Steps")[0]
    known = set(known_event_ids)
    invented = set()
    for line in body.splitlines():
        for n in re.findall(r"\b\d{4}\b", line):
            num = int(n)
            if num in known or num == CURRENT_YEAR:
                continue
            if re.search(
                rf"\b(?:no|not|without|absence)\s+[:(\w\s,.-]*?\b{n}\b",
                line,
                re.IGNORECASE,
            ):
                continue  # negated mention, not a claimed finding
            invented.add(num)
    return sorted(invented)


_SEVERITY_LABEL_RE = re.compile(r"severity[^\n]{0,140}", re.IGNORECASE)


def max_severity_in(text: str):
    """Highest severity RATING the model assigned (scans Severity: labels).

    Only levels that appear on/near an actual "Severity:" rating line count —
    generic adjectives like "monitor this critical event" or "critical
    evidence" are NOT treated as a rating.
    """
    hits = set()
    for chunk in _SEVERITY_LABEL_RE.findall(text):
        for lvl in SEVERITY_LEVELS:
            if re.search(rf"\b{lvl}\b", chunk, re.IGNORECASE):
                hits.add(lvl)
    if not hits:
        return None
    return max(hits, key=lambda x: SEVERITY_LEVELS[x])


def findings_count(text: str) -> int:
    """Number of structured findings the model produced ('Event #N' / 'Event N')."""
    return len(re.findall(r"Event\s*#?\s*\d+", text))


def check_analysis(text: str, known_event_ids, expected_max: str):
    """Run all quality checks. Returns (verdict, detail rows)."""
    rows = []

    miss = missing_sections(text)
    rows.append(("sections 5/5", "PASS" if not miss else "FAIL", "; ".join(miss) or ""))
    sections_ok = not miss

    hall = hallucinated_event_ids(text, known_event_ids)
    rows.append(
        ("no invented Event IDs", "PASS" if not hall else "WARN",
         "invented: %s" % hall if hall else "")
    )

    actual = max_severity_in(text)
    if actual is None:
        posture, posture_note = "WARN", "no severity level mentioned"
    else:
        diff = SEVERITY_LEVELS[actual] - SEVERITY_LEVELS[expected_max]
        if diff >= 2:
            posture, posture_note = (
                "WARN",
                f"overstated ({actual} vs expected {expected_max})",
            )
        elif diff <= -2:
            posture, posture_note = (
                "WARN",
                f"understated ({actual} vs expected {expected_max})",
            )
        else:
            posture, posture_note = "PASS", f"matches/~expected ({actual})"
    rows.append(("risk posture", posture, posture_note))

    rows.append(("findings", "INFO", f"{findings_count(text)}"))

    if not sections_ok:
        verdict = "FAIL"
    elif any(r[1] == "WARN" for r in rows):
        verdict = "WARN"
    else:
        verdict = "PASS"
    return verdict, rows


def self_test() -> None:
    """Offline check of the checkers themselves (no LLM, no network)."""
    good = (
        "## 1. Plain-English Summary\n"
        "## 5. Confidence & Limitations\n"
        "Event #1 (Event ID 4625) Severity: High (8/10)\n"
    )
    assert missing_sections(good) == [
        "## 2. Security Events (ranked by risk)",
        "## 3. What These Events Suggest",
        "## 4. Recommended Next Steps",
    ], missing_sections(good)
    # Invented ID in the summary/findings body is flagged...
    assert hallucinated_event_ids("Event ID 9999", {4625}) == [9999]
    # ...but advice in Next Steps may mention other IDs without a flag.
    text_with_advice = (
        "## 1. Plain-English Summary\n## 2. Security Events (ranked by risk)\n"
        "## 3. What These Events Suggest\n## 4. Recommended Next Steps\n"
        "check for subsequent 4720/4728 account changes"
    )
    assert hallucinated_event_ids(text_with_advice, {4625}) == []
    # ...and a NEGATED mention ("no 4625 events") is a correct absence note.
    assert hallucinated_event_ids("There were (no 4625 events) observed", {4672}) == []
    assert hallucinated_event_ids("4625 events were observed", {4672}) == [4625]
    # Only Severity: RATINGS count, not generic adjectives.
    assert max_severity_in("Severity: Low\nSeverity: Info") == "low"
    assert max_severity_in("This is critical monitoring advice.") is None
    assert max_severity_in("**Severity:** Critical (10/10)") == "critical"
    assert findings_count("Event #1\nEvent 2\nEvent ID 3") == 2

    v, rows = check_analysis(
        "## 1. Plain-English Summary\n"
        "## 5. Confidence & Limitations\n"
        "Event ID 1 critical",
        [1],
        "high",
    )
    assert v == "FAIL", "missing-section failure not detected"
    # Understated posture (expected high, actual low) -> WARN. Full sections so
    # the verdict reflects the posture deviation, not a missing-section FAIL.
    full = (
        "## 1. Plain-English Summary\n"
        "## 2. Security Events (ranked by risk)\n"
        "## 3. What These Events Suggest\n"
        "## 4. Recommended Next Steps\n"
        "## 5. Confidence & Limitations\n"
        "Event #1 (Event ID 4625) Severity: Low (2/10)\n"
    )
    v, rows = check_analysis(full, [4625], "high")
    assert v == "WARN", "posture understatement not detected"
    print("SELF-TEST OK - quality-check helpers behave as expected")
def run_scenario(scen: dict, provider: LLMProvider, force: bool, suffix: str = "") -> dict:
    json_path = Path(scen["json"])
    md_path = Path(scen["md"])
    if suffix:
        md_path = md_path.with_name(f"{md_path.stem}.{suffix}{md_path.suffix}")
    if not json_path.exists():
        raise FileNotFoundError(f"Scenario JSON missing: {json_path}")

    if md_path.exists() and not force:
        print(f"[*] {md_path.name} exists - reusing (--force to re-run)")
    else:
        print(f"[*] Analyzing {scen['name']} ... (may take minutes)")
        t0 = time.time()
        used_model, _ = analyze_event_log_file(
            input_file=scen["json"],
            output_file=md_path,  # keep suffix/serialized outputs apart
            title=f"Day 16 Event Log LLM Analysis - {scen['name']}",
            provider=provider,
        )
        print(f"[+] {scen['name']}: {used_model} in {time.time() - t0:.1f}s -> {md_path.name}")

    text = md_path.read_text(encoding="utf-8")
    known_ids = {
        e["event_id"]
        for e in json.loads(json_path.read_text(encoding="utf-8"))["events"]
    }
    verdict, rows = check_analysis(text, known_ids, scen["expected_max"])
    return {
        "name": scen["name"],
        "md": md_path.name,
        "size": len(text),
        "verdict": verdict,
        "rows": rows,
        "note": scen["note"],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Day 16 event-log LLM validation")
    ap.add_argument("--provider", default="ollama", choices=["ollama", "gemini"],
                    help="LLM provider to test against")
    ap.add_argument("--force", action="store_true", help="Re-run saved outputs")
    ap.add_argument("--limit", type=int, default=None, help="Only first N scenarios")
    ap.add_argument("--suffix", default="", help="Suffix for output files, e.g. gemini")
    ap.add_argument("--self-test", action="store_true", help="Offline checker tests")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return

    provider = LLMProvider(args.provider)
    if provider is LLMProvider.OLLAMA:
        models = list_ollama_models()
        print(f"[+] Ollama reachable; models: {models}")
        if not models:
            raise SystemExit("No Ollama models installed - pull one first.")
        # Warm the model so first-call latency doesn't dominate timing.
        from sentinelai.prompt_engine import analyze_event_log_data
        print("[*] Warming model ...")
        analyze_event_log_data(
            {"source": "warmup", "host": "warmup", "count": 0, "events": [
                {"event_id": 1, "message": "Reply with: ready"}]},
            provider=LLMProvider.OLLAMA,
        )
    else:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        if not os.getenv("GEMINI_API_KEY"):
            raise SystemExit(
                "GEMINI_API_KEY not set; use --provider ollama for local testing."
            )

    print("=" * 76)
    print("SentinelAI Day 16 - Event Log LLM validation")
    print("=" * 76)

    results = []
    for scen in SCENARIOS[: args.limit]:
        try:
            r = run_scenario(scen, provider, args.force, args.suffix)
        except Exception as exc:  # network/API failures must not abort the batch
            print(f"[-] {scen['name']}: FAILED - {exc}")
            r = {
                "name": scen["name"],
                "md": "-",
                "size": 0,
                "verdict": "FAIL",
                "rows": [("exception", "FAIL", str(exc))],
                "note": scen["note"],
            }
        results.append(r)

    print("\n" + "=" * 76)
    print("SUMMARY - provider:", provider.value)
    print("=" * 76)
    for r in results:
        print(f"\n[{r['verdict']:>4}] {r['name']:<11} {r['md']} ({r['size']} bytes)")
        print(f"        {r['note']}")
        for label, status, note in r["rows"]:
            print(f"        - {label:<22} {status:<5} {note}")

    failed = [r["name"] for r in results if r["verdict"] == "FAIL"]
    if failed:
        raise SystemExit(f"FAILED scenarios: {', '.join(failed)}")
    print("\nDay 16 validation complete.")


if __name__ == "__main__":
    main()
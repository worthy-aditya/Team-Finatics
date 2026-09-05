"""Day 25 (Week 4): ONE-COMMAND end-to-end pipeline test.

Drives the REAL CLI as a black box (subprocess) through the full pipeline
from the sprint plan -- full scan + logs + AI + report -- with per-stage
pass criteria, so any wiring regression between commands is caught:

  1. SCAN    scan --target <t> --fast --json-file <tmp>/scan.json
             PASS: rc=0, JSON loads, has hosts[] + summary
  2. LOGS    logs --sample -o <tmp>/events.json   (+ --json stdout purity)
             PASS: rc=0, schema JSON count>=3, threat_level present,
                   and `--json` stdout parses as pure JSON
  3. AI      analyze -i <tmp>/scan.json --kind scan --llm <p> -o analysis.md
             PASS: rc=0, Markdown with all 5 section headers
  4. REPORT  report -i <tmp>/scan.json --format json|text
             PASS: rc=0, report JSON loads with target/details,
                   text report contains the report banner

Usage (from the repo root):
  py tests/test_e2e_pipeline.py                  # live run, ollama, 127.0.0.1
  py tests/test_e2e_pipeline.py --llm gemini     # analysis via Gemini API
  py tests/test_e2e_pipeline.py --use-fixture    # skip live nmap (scan_results.json)
  py tests/test_e2e_pipeline.py --skip-llm       # stages 1,2,4 only (no LLM)
  py tests/test_e2e_pipeline.py --cli both       # pipeline on BOTH CLIs

pytest mode: skipped unless SENTINELAI_RUN_E2E=1 (this test is live, slow,
and needs nmap + a reachable target; run it explicitly as a script instead).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DRIVERS = {
    "root": [sys.executable, str(ROOT / "sentinelai.py")],
    "pkg": [sys.executable, "-m", "sentinelai.cli"],
}

SCAN_SECTIONS = [f"## {i}." for i in range(1, 6)]  # 5-section scan template


def _run(args, timeout):
    """Run a CLI stage from the repo root; return (rc, stdout, stderr)."""
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"  # deterministic child output encoding
    try:
        proc = subprocess.run(
            args, cwd=str(ROOT), capture_output=True,
            timeout=timeout, env=env,
        )
        out = proc.stdout.decode("utf-8-sig", errors="replace")
        err = proc.stderr.decode("utf-8-sig", errors="replace")
        return proc.returncode, out, err
    except subprocess.TimeoutExpired:
        return None, "", f"TIMEOUT after {timeout}s"


def _fail(name, detail):
    print(f"  FAIL  {name}")
    for line in detail:
        print(f"          {line}")
    return {"name": name, "ok": False, "detail": detail}


def _pass(name, detail):
    print(f"  PASS  {name}  ({detail})")
    return {"name": name, "ok": True, "detail": detail}


def stage_scan(driver, tmp, target, use_fixture):
    """Stage 1: scan -> scan.json (or fixture copy when --use-fixture)."""
    scan_file = tmp / "scan.json"
    if use_fixture:
        shutil.copyfile(ROOT / "scan_results.json", scan_file)
        return _pass("1/4 SCAN   [fixture]", f"{scan_file.name} (no live nmap)")

    args = driver + ["scan", "--target", target, "--fast",
                     "--json-file", str(scan_file), "--yes"]
    rc, out, err = _run(args, timeout=420)
    if rc != 0:
        return _fail("1/4 SCAN", [f"rc={rc}", (err or out)[-300:]])
    try:
        data = json.loads(scan_file.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return _fail("1/4 SCAN", [f"scan.json unreadable: {exc}", out[-200:]])
    if not isinstance(data.get("hosts"), list):
        return _fail("1/4 SCAN", ["'hosts' missing or not a list"])
    if "summary" not in data:
        return _fail("1/4 SCAN", ["'summary' missing from scan JSON"])
    n_hosts = len(data["hosts"])
    n_open = data["summary"].get("total_open_ports", "?")
    return _pass("1/4 SCAN", f"hosts={n_hosts} open_ports={n_open}")


def stage_logs(driver, tmp):
    """Stage 2: logs --sample -> schema file + --json stdout purity."""
    events_file = tmp / "events.json"
    rc, out, err = _run(driver + ["logs", "--sample", "-o", str(events_file)], 60)
    if rc != 0:
        return _fail("2/4 LOGS", [f"rc={rc}", (err or out)[-300:]])
    try:
        doc = json.loads(events_file.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return _fail("2/4 LOGS", [f"events.json unreadable: {exc}"])
    if doc.get("count", 0) < 3 or not doc.get("events"):
        return _fail("2/4 LOGS", ["expected count>=3 with non-empty events"])

    # Machine path must be pure JSON on stdout (Day 24 contract).
    rc2, out2, err2 = _run(driver + ["logs", "--sample", "--json"], 60)
    if rc2 != 0:
        return _fail("2/4 LOGS", [f"--json rc={rc2}", (err2 or out2)[-300:]])
    try:
        pure = json.loads(out2)
    except Exception:
        return _fail("2/4 LOGS", ["--json stdout is not pure JSON",
                                  out2[:120].replace("\n", " ")])
    if "threat_level" not in pure:
        return _fail("2/4 LOGS", ["--json output missing threat_level"])
    return _pass("2/4 LOGS", f"events={doc['count']} threat={pure.get('threat_level')}")


def stage_ai(driver, tmp, llm, skip_llm):
    """Stage 3: analyze -> Markdown with all 5 section headers."""
    if skip_llm:
        print("  SKIP  3/4 AI     (--skip-llm)")
        return {"name": "3/4 AI", "ok": True, "detail": "skipped"}
    analysis_file = tmp / "analysis.md"
    args = driver + ["analyze", "-i", str(tmp / "scan.json"), "--kind", "scan",
                     "--llm", llm, "-o", str(analysis_file)]
    rc, out, err = _run(args, timeout=900)
    if rc != 0:
        return _fail("3/4 AI", [f"rc={rc}", (err or out)[-400:]])
    md = analysis_file.read_text(encoding="utf-8-sig", errors="replace")
    missing = [s for s in SCAN_SECTIONS if s not in md]
    if missing:
        return _fail("3/4 AI", [f"missing section headers: {missing}"])
    if len(md) < 500:
        return _fail("3/4 AI", [f"analysis suspiciously short ({len(md)} chars)"])
    return _pass("3/4 AI", f"llm={llm} 5/5 sections, {len(md)} chars")


def stage_report(driver, tmp):
    """Stage 4: report -> JSON + text artifacts from the scan."""
    base = tmp / "e2e_report"
    rc, out, err = _run(driver + ["report", "-i", str(tmp / "scan.json"),
                                  "-o", str(base), "--format", "json"], 60)
    if rc != 0:
        return _fail("4/4 REPORT", [f"json rc={rc}", (err or out)[-300:]])
    try:
        rep = json.loads((tmp / "e2e_report.json").read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return _fail("4/4 REPORT", [f"report JSON unreadable: {exc}"])
    if "details" not in rep or "scan_summary" not in rep:
        return _fail("4/4 REPORT", ["report JSON missing details/scan_summary"])

    rc2, out2, err2 = _run(driver + ["report", "-i", str(tmp / "scan.json"),
                                     "-o", str(base), "--format", "text"], 60)
    if rc2 != 0:
        return _fail("4/4 REPORT", [f"text rc={rc2}", (err2 or out2)[-300:]])
    txt = (tmp / "e2e_report.txt").read_text(encoding="utf-8-sig", errors="replace")
    if "SENTINELAI NETWORK SCAN REPORT" not in txt:
        return _fail("4/4 REPORT", ["text report missing banner"])
    return _pass("4/4 REPORT", "json + text artifacts valid")


def run_pipeline(cli_name="root", target="127.0.0.1", llm="ollama",
                 use_fixture=False, skip_llm=False, tmp_dir=None):
    """Run all stages; return (results, elapsed_seconds)."""
    driver = DRIVERS[cli_name]
    started = time.time()
    print(f"\n=== SentinelAI one-command E2E pipeline | cli={cli_name} "
          f"target={target} llm={llm} ===")
    with tempfile.TemporaryDirectory(prefix="sentinelai_e2e_") as td:
        tmp = Path(tmp_dir or td)
        results = [
            stage_scan(driver, tmp, target, use_fixture),
            stage_logs(driver, tmp),
            stage_ai(driver, tmp, llm, skip_llm),
            stage_report(driver, tmp),
        ]
    elapsed = time.time() - started
    ok = all(r["ok"] for r in results)
    verdict = "PASSED" if ok else "FAILED"
    print(f"\nE2E PIPELINE {verdict} ({sum(r['ok'] for r in results)}/4 stages) "
          f"in {elapsed:.1f}s [cli={cli_name}]")
    return results, elapsed


def _main():
    ap = argparse.ArgumentParser(description="SentinelAI one-command E2E pipeline test")
    ap.add_argument("--target", default="127.0.0.1", help="Scan target (default: 127.0.0.1)")
    ap.add_argument("--llm", default="ollama", choices=["gemini", "ollama"],
                    help="LLM provider for the AI stage (default: ollama)")
    ap.add_argument("--cli", default="root", choices=["root", "pkg", "both"],
                    help="Which CLI entry point to drive (default: root)")
    ap.add_argument("--use-fixture", action="store_true",
                    help="Skip live nmap; reuse the committed scan_results.json fixture")
    ap.add_argument("--skip-llm", action="store_true", help="Run stages 1, 2, 4 only")
    args = ap.parse_args()

    clis = ["root", "pkg"] if args.cli == "both" else [args.cli]
    all_ok = True
    for c in clis:
        results, _ = run_pipeline(
            cli_name=c, target=args.target, llm=args.llm,
            use_fixture=args.use_fixture, skip_llm=args.skip_llm,
        )
        all_ok &= all(r["ok"] for r in results)
    sys.exit(0 if all_ok else 1)


def test_e2e_pipeline():
    """pytest entry: opt-in via SENTINELAI_RUN_E2E=1 (live and slow)."""
    if os.environ.get("SENTINELAI_RUN_E2E") != "1":
        print("SKIP live E2E (set SENTINELAI_RUN_E2E=1 to enable)")
        return
    results, _ = run_pipeline(cli_name="root", llm="ollama")
    assert all(r["ok"] for r in results), results


if __name__ == "__main__":
    _main()
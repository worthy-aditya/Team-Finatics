"""
tests/demo_rehearsal.py
Day 27 (Week 4): timed demo rehearsal — runs the EXACT hackathon demo flow
(scan + logs + AI + report) end-to-end and enforces the sprint gate:
under 3 minutes total, zero crashes.

Reuses the Day 25 E2E helpers (_run/_pass/_fail/DRIVERS) — no parallel logic.
Not auto-collected by pytest (no test_ prefix); a live, slow, opt-in tool:

    python tests/demo_rehearsal.py                    # full timed flow
    python tests/demo_rehearsal.py --skip-llm         # timing dry run
    python tests/demo_rehearsal.py --use-fixture      # skip live nmap
    python tests/demo_rehearsal.py --keep             # keep artifacts in ./demo_artifacts
"""
import argparse
import json
import shutil
import sys
import time
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_DIR))
sys.path.insert(0, str(TESTS_DIR.parent))

from test_e2e_pipeline import DRIVERS, SCAN_SECTIONS, _run  # noqa: E402

TIME_LIMIT_S = 180  # sprint gate: demo must fit under 3 minutes


def _preflight(driver, scan_llm):
    """Untimed checks that the demo environment is actually demo-ready.

    Returns (issues, effective_scan_llm): if the scan-analysis leg is set to
    gemini but no key is configured, it falls back to ollama with a notice
    (which likely pushes the total over the 3-minute gate).
    """
    issues = []
    try:
        import requests
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        models = [m.get("name", "") for m in r.json().get("models", [])]
        if not models:
            issues.append("Ollama reachable but no models installed (ollama pull llama3)")
    except Exception:
        issues.append("Ollama not reachable on http://localhost:11434 (start the app/server)")
    rc, _out, _err = _run(["nmap", "--version"], 30)
    if rc != 0:
        issues.append("nmap not on PATH (scanning step will crash)")
    rc2, _o2, _e2 = _run(driver + ["--help"], 30)
    if rc2 != 0:
        issues.append("sentinelai CLI itself failed to start")
    if scan_llm == "gemini":
        from dotenv import load_dotenv
        load_dotenv()
        import os
        if not os.getenv("GEMINI_API_KEY"):
            print("  NOTICE   GEMINI_API_KEY not set — scan-analysis leg falls back to ollama")
            scan_llm = "ollama"
    return issues, scan_llm


def run_rehearsal(cli_name="root", target="127.0.0.1", llm="ollama",
                  scan_llm="gemini", use_fixture=False, skip_llm=False,
                  max_seconds=TIME_LIMIT_S, keep=False):
    driver = DRIVERS[cli_name]
    print(f"\n=== SentinelAI demo rehearsal | cli={cli_name} target={target} "
          f"llm={llm} scan-llm={scan_llm} limit={max_seconds}s ===")

    issues, scan_llm = _preflight(driver, scan_llm)
    for msg in issues:
        print(f"  BLOCKER  {msg}")
    if issues:
        print("\nREHEARSAL BLOCKED — fix the environment issues above, then rerun.")
        return False, {}

    if keep:
        out_dir = TESTS_DIR.parent / "demo_artifacts"
        if out_dir.exists():
            shutil.rmtree(out_dir)
        out_dir.mkdir(parents=True)
    else:
        import tempfile
        out_dir = Path(tempfile.mkdtemp(prefix="sentinelai_demo_"))
    print(f"  artifacts -> {out_dir}\n")

    steps = []  # (name, seconds, ok, detail)

    def timed(name, args, timeout, check):
        t0 = time.perf_counter()
        rc, out, err = _run(args, timeout)
        secs = time.perf_counter() - t0
        ok, detail = check(rc, out, err)
        steps.append((name, secs, ok, detail))
        flag = "PASS " if ok else "FAIL "
        print(f"  {flag} {secs:6.1f}s  {name:28s} {detail}")
        return ok

    scan_json = out_dir / "demo_scan.json"

    if use_fixture:
        shutil.copyfile(TESTS_DIR.parent / "scan_results.json", scan_json)
        steps.append(("1/5 SCAN (fixture)", 0.0, True, "committed fixture reused"))
        print("  PASS    0.0s  1/5 SCAN (fixture)            committed fixture reused")
    else:
        def chk_scan(rc, out, err):
            if rc != 0:
                return False, f"rc={rc} {(err or out)[-160:]}"
            data = json.loads(scan_json.read_text(encoding="utf-8-sig"))
            hosts = data.get("hosts", [])
            return (bool(hosts), f"hosts={len(hosts)}")
        timed("1/5 SCAN (--fast)", driver + ["scan", "--target", target, "--fast",
              "--json-file", str(scan_json)], 300, chk_scan)

    def chk_logs_json(rc, out, err):
        if rc != 0:
            return False, f"rc={rc}"
        try:
            doc = json.loads(out)
        except Exception:
            return False, "stdout not pure JSON"
        return (len(doc.get("events", [])) > 0, f"events={len(doc.get('events', []))}")

    timed("2/5 logs --sample --json", driver + ["logs", "--sample", "--json"],
          60, chk_logs_json)

    if skip_llm:
        steps.append(("3/5 logs --analyze", 0.0, True, "skipped (--skip-llm)"))
        steps.append(("4/5 analyze scan", 0.0, True, "skipped (--skip-llm)"))
        print("  SKIP          3/5 logs --analyze              (--skip-llm)")
        print("  SKIP          4/5 analyze scan                (--skip-llm)")
    else:
        def chk_logs_ai(rc, out, err):
            if rc != 0:
                return False, f"rc={rc} {(err or out)[-160:]}"
            return (len(out) > 300, f"{len(out)} chars of analysis")
        timed("3/5 logs --sample --analyze", driver + ["logs", "--sample",
              "--analyze", "--llm", llm], 600, chk_logs_ai)

        analysis_md = out_dir / "demo_analysis.md"

        def chk_analyze(rc, out, err):
            if rc != 0:
                return False, f"rc={rc} {(err or out)[-160:]}"
            md = analysis_md.read_text(encoding="utf-8-sig", errors="replace")
            missing = [s for s in SCAN_SECTIONS if s not in md]
            if missing:
                return False, f"missing sections: {missing}"
            return (len(md) >= 500, f"5/5 sections, {len(md)} chars")
        timed(f"4/5 analyze scan [{scan_llm}]", driver + ["analyze", "-i",
              str(scan_json), "--kind", "scan", "--llm", scan_llm,
              "-o", str(analysis_md)], 600, chk_analyze)

    report_base = str(out_dir / "demo_report")

    def chk_report(rc, out, err):
        if rc != 0:
            return False, f"rc={rc} {(err or out)[-160:]}"
        txt = (out_dir / "demo_report.txt").read_text(encoding="utf-8-sig",
                                                      errors="replace")
        return ("SENTINELAI NETWORK SCAN REPORT" in txt, "text report valid")
    timed("5/5 report", driver + ["report", "-i", str(scan_json), "-o",
          report_base, "--format", "text"], 120, chk_report)

    total = sum(s for _n, s, _ok, _d in steps)
    failed = [n for n, _s, ok, _d in steps if not ok]
    under = total <= max_seconds
    print(f"\n  TOTAL {total:6.1f}s of {max_seconds}s budget "
          f"({'UNDER 3 MINUTES' if under else 'OVER 3 MINUTES'})")
    if failed:
        print(f"  crashed steps: {failed}")
    verdict = "REHEARSAL PASSED" if (not failed and under) else "REHEARSAL FAILED"
    print(f"  {verdict}  [artifacts in {out_dir}]")
    return (not failed and under), {"total_s": total, "steps": steps}


def _main():
    ap = argparse.ArgumentParser(description="Timed SentinelAI demo rehearsal")
    ap.add_argument("--target", default="127.0.0.1")
    ap.add_argument("--llm", default="ollama", choices=["gemini", "ollama"],
                    help="LLM for the private event-log leg (default: ollama)")
    ap.add_argument("--scan-llm", default="gemini", choices=["gemini", "ollama"],
                    help="LLM for the scan-report leg (default: gemini — keeps the "
                         "demo under 3 minutes; auto-falls-back to ollama w/o key)")
    ap.add_argument("--cli", default="root", choices=["root", "pkg"])
    ap.add_argument("--max-seconds", type=int, default=TIME_LIMIT_S)
    ap.add_argument("--use-fixture", action="store_true")
    ap.add_argument("--skip-llm", action="store_true")
    ap.add_argument("--keep", action="store_true",
                    help="keep artifacts in ./demo_artifacts instead of a temp dir")
    args = ap.parse_args()
    ok, _info = run_rehearsal(cli_name=args.cli, target=args.target, llm=args.llm,
                              scan_llm=args.scan_llm, use_fixture=args.use_fixture,
                              skip_llm=args.skip_llm, max_seconds=args.max_seconds,
                              keep=args.keep)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    _main()

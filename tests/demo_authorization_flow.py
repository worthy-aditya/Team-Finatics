"""
tests/demo_authorization_flow.py
Day 37 (Feature Sprint): timed live-demo rehearsal of the two-layer
authorization flow — the team-sync deliverable "Full authorization flow
demoed live to team".

Runs the EXACT flow a team member will see, end to end with ZERO mocks:

  Stage 0  preflight (nmap on PATH, CLI starts)
  Stage 1  token generation + .well-known publish + local HTTP server
  Stage 2  GRANT  — real CLI: consent attestation (typed via stdin) ->
           domain verification (real HTTP fetch) -> authorized -> nmap scan
  Stage 3  DENY  — same command, WRONG token -> blocked before any scan
  Stage 4  GUARD — --active --yes rejected up-front (Day 32 rule)
  Stage 5  audit trail — consent_audit_log.jsonl captured every attempt

Not auto-collected by pytest (no test_ prefix); a live, slow, opt-in tool
(Day 27 demo_rehearsal.py conventions: timed gate, staged PASS/FAIL record):

    python tests/demo_authorization_flow.py            # full timed rehearsal
    python tests/demo_authorization_flow.py --keep     # keep artifacts
"""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sentinelai.consent import expected_attestation  # noqa: E402
from sentinelai.domain_verify import (  # noqa: E402
    generate_verify_token,
    verify_token_publish_line,
)

TIME_LIMIT_S = 180  # team-sync gate: the demo must fit under 3 minutes
CLI = ROOT / "sentinelai.py"
RESULTS = []


class _Handler(BaseHTTPRequestHandler):
    """Serve the .well-known verify file; silent (no request logs)."""

    body = b""

    def do_GET(self):
        code = 200 if self.path.endswith("sentinelai-verify.txt") else 404
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(self.body)))
        self.end_headers()
        self.wfile.write(self.body)

    def log_message(self, *args):
        pass


def _run(argv, timeout, stdin_text="", cwd=None):
    """Run a subprocess; return (exit_code, combined_output)."""
    proc = subprocess.run(
        argv,
        input=stdin_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        cwd=str(cwd) if cwd else None,
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def _stage(name, check):
    """Run one demo stage; record + print PASS/FAIL (demo_rehearsal style)."""
    t0 = time.time()
    try:
        note = check()
        RESULTS.append((name, True, time.time() - t0))
        print(f"  PASS  {name} ({time.time() - t0:.1f}s)"
              + (f" — {note}" if note else ""))
    except Exception as exc:  # noqa: BLE001 - demo tool: report and stop
        RESULTS.append((name, False, time.time() - t0))
        print(f"  FAIL  {name} ({time.time() - t0:.1f}s) — {exc}")
        raise SystemExit(1)


_token_holder = {}
_server_holder = {}


def preflight():
    issues = []
    rc, _out = _run(["nmap", "--version"], 30)
    if rc != 0:
        issues.append("nmap not on PATH (scan stage will fail)")
    rc2, out2 = _run([sys.executable, str(CLI), "--version"], 30)
    if rc2 != 0:
        issues.append("sentinelai CLI failed to start")
    if issues:
        raise AssertionError("; ".join(issues))
    return out2.strip()


def publish_and_serve():
    token = generate_verify_token()
    _token_holder["token"] = token
    _Handler.body = (verify_token_publish_line(token) + "\n").encode("utf-8")
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    _server_holder["server"] = server
    threading.Thread(target=server.serve_forever, daemon=True).start()
    _server_holder["port"] = server.server_address[1]
    return f"token={token[:8]}… http://127.0.0.1:{server.server_address[1]}"


def grant_path(run_dir):
    token = _token_holder["token"]
    target = f"http://127.0.0.1:{_server_holder['port']}"
    attestation = expected_attestation(target)
    rc, out = _run(
        [sys.executable, str(CLI), "scan", "--target", target, "--active",
         "--verify-token", token, "--fast"],
        240,
        stdin_text=attestation + "\n",
        cwd=run_dir,
    )
    if rc != 0:
        raise AssertionError(f"exit={rc}: {out[-300:]}")
    if "Both authorization checks passed" not in out:
        raise AssertionError("authorization banner missing")
    if "Scan completed successfully" not in out:
        raise AssertionError("scan stage did not run")
    return "consent typed + domain verified + nmap ran"


def deny_domain(run_dir):
    token = _token_holder["token"]
    target = f"http://127.0.0.1:{_server_holder['port']}"
    attestation = expected_attestation(target)
    rc, out = _run(
        [sys.executable, str(CLI), "scan", "--target", target, "--active",
         "--verify-token", token[:8] + "-wrong", "--fast"],
        240,
        stdin_text=attestation + "\n",
        cwd=run_dir,
    )
    if rc != 0:
        raise AssertionError("deny path should exit 0 with blocked message")
    if "token_mismatch" not in out:
        raise AssertionError("expected token_mismatch block")
    if "Scan completed successfully" in out:
        raise AssertionError("scan ran despite failed verification")
    return "blocked with token_mismatch; no scan ran"


def guard_yes():
    target = f"http://127.0.0.1:{_server_holder['port']}"
    rc, out = _run(
        [sys.executable, str(CLI), "scan", "--target", target, "--active", "--yes"],
        60,
    )
    if rc == 0:
        raise AssertionError("--active --yes must be rejected")
    if "--yes" not in out:
        raise AssertionError("expected the Day 32 --yes rejection message")
    return "exit != 0, --yes message present"


def audit_trail(run_dir):
    audit = Path(run_dir) / "consent_audit_log.jsonl"
    if not audit.exists():
        raise AssertionError("consent_audit_log.jsonl missing from run dir")
    records = [json.loads(line) for line in
               audit.read_text(encoding="utf-8").splitlines() if line.strip()]
    decisions = [r["decision"] for r in records]
    # Stage 2 grants consent + verifies the domain. Stage 3 attests FRESH
    # (by design every run re-attests) and is then denied on token mismatch.
    expected = ["granted", "verified", "granted", "denied"]
    if decisions != expected:
        raise AssertionError(f"unexpected decisions: {decisions}")
    return f"{len(records)} records: " + " -> ".join(
        f"{r['event']}:{r['decision']}" for r in records)


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keep", action="store_true", help="keep run artifacts")
    args = parser.parse_args()

    print(f"=== Day 37 authorization-flow demo rehearsal (gate: {TIME_LIMIT_S}s) ===")
    run_dir = Path(tempfile.mkdtemp(prefix="sentinelai_day37_demo_"))
    t0 = time.time()
    all_ok = False

    try:
        _stage("0 preflight", preflight)
        _stage("1 token + .well-known publish + local server", publish_and_serve)
        _stage("2 GRANT: consent + domain verify + scan (real CLI)",
               lambda: grant_path(run_dir))
        _stage("3 DENY: wrong token blocks before scan (real CLI)",
               lambda: deny_domain(run_dir))
        _stage("4 GUARD: --active --yes rejected", guard_yes)
        _stage("5 audit trail (grant -> verified -> fresh grant -> denied)",
               lambda: audit_trail(run_dir))
    except SystemExit:
        pass  # stage already printed FAIL; fall through to the summary
    finally:
        server = _server_holder.get("server")
        if server:
            server.shutdown()
            server.server_close()
        total = time.time() - t0
        print("-" * 74)
        for name, ok, seconds in RESULTS:
            print(f"  {'PASS' if ok else 'FAIL'}  {name} ({seconds:.1f}s)")
        print("-" * 74)
        all_ok = bool(RESULTS) and all(ok for _n, ok, _s in RESULTS)
        verdict = "PASSED" if all_ok and total <= TIME_LIMIT_S else "FAILED"
        print(f"TOTAL {total:.1f}s / {TIME_LIMIT_S}s gate — {verdict}")

        if args.keep and all_ok:
            kept = ROOT / "demo_day37_artifacts"
            if kept.exists():
                shutil.rmtree(kept)
            shutil.copytree(run_dir, kept)
            print(f"  artifacts kept in {kept}")
        shutil.rmtree(run_dir, ignore_errors=True)

    raise SystemExit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
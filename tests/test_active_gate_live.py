"""Day 34 LIVE end-to-end test for the --active gate (REAL HTTP, no mocks).

Spins a real local ThreadingHTTPServer serving .well-known/sentinelai-verify.txt
and runs authorize_active_testing with the REAL default urllib fetcher. Only
the consent prompt is injected, because typing an attestation is a keyboard
interaction, not a network one. Proves the full authorization chain:
consent gate -> domain verification over real HTTP -> authorized.
"""
import json
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sentinelai.active_gate import authorize_active_testing
from sentinelai.consent import expected_attestation
from sentinelai.domain_verify import generate_verify_token, verify_token_publish_line

TOKEN = generate_verify_token()
WRONG_TOKEN = generate_verify_token()
PUBLISH_LINE = verify_token_publish_line(TOKEN)


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        if path.endswith("sentinelai-verify.txt"):
            code, body = 200, PUBLISH_LINE.encode("utf-8")
        else:
            code, body = 404, b"not found"
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # keep test output clean
        pass


def _serve():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def _run_gate(target, token, audit):
    def prompt(text, **kwargs):
        return expected_attestation(target)

    return authorize_active_testing(
        target,
        verify_token=token,
        scheme="http",  # local lab server is plain HTTP
        audit_path=str(audit),
        prompt=prompt,
    )  # NOTE: no fetch= injection - the real urllib fetcher runs


def test_live_gate_authorizes_over_real_http():
    server = _serve()
    try:
        target = f"http://127.0.0.1:{server.server_address[1]}"
        with tempfile.TemporaryDirectory() as td:
            audit = Path(td) / "consent_audit_log.jsonl"
            auth = _run_gate(target, TOKEN, audit)
            assert auth.authorized is True, auth.blocked_reason
            assert auth.consent.granted is True
            assert auth.domain is not None and auth.domain.verified is True
            assert auth.domain.status_code == 200
            assert auth.blocked_reason == ""
            with open(audit, encoding="utf-8") as fh:
                records = [json.loads(line) for line in fh if line.strip()]
            assert [r["event"] for r in records] == ["consent_attempt", "domain_verify"]
            assert [r["decision"] for r in records] == ["granted", "verified"]
    finally:
        server.shutdown()
        server.server_close()


def test_live_gate_denies_wrong_token_over_real_http():
    server = _serve()
    try:
        target = f"http://127.0.0.1:{server.server_address[1]}"
        with tempfile.TemporaryDirectory() as td:
            audit = Path(td) / "consent_audit_log.jsonl"
            auth = _run_gate(target, WRONG_TOKEN, audit)
            assert auth.authorized is False
            assert "token_mismatch" in auth.blocked_reason
            with open(audit, encoding="utf-8") as fh:
                records = [json.loads(line) for line in fh if line.strip()]
            assert [r["decision"] for r in records] == ["granted", "denied"]
    finally:
        server.shutdown()
        server.server_close()


def _main():
    # Windows consoles/pipe captures default to cp1252; the consent panel
    # renders Unicode, so force UTF-8 for direct (non-pytest) runs.
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
    print(f"ALL {len(fns) - failures}/{len(fns)} active-gate LIVE TESTS PASSED (real HTTP)")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    _main()
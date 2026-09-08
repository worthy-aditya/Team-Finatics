"""Day 33 LIVE check - verify_domain_ownership() against a real test file.

This is the Day 33 deliverable: a real HTTP fetch from verify_domain_ownership()
against a locally-served .well-known/sentinelai-verify.txt file (no mocks, no
internet - loopback only). It proves the module works end-to-end:

  1. grant  - matching token file  -> verified
  2. deny   - wrong token file     -> token_mismatch
  3. deny   - file removed         -> file_not_found

Run as a script or via pytest. The local server uses an ephemeral 127.0.0.1
port, so nothing outside this machine is touched.
"""
import json
import sys
import tempfile
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sentinelai.domain_verify import (
    generate_verify_token,
    verify_domain_ownership,
    verify_token_publish_line,
)


class _QuietHandler(SimpleHTTPRequestHandler):
    """Serve files but stay silent (no stderr request logs)."""

    def log_message(self, *args):  # noqa: ANN002 - override to suppress noise
        pass


def _write(root: Path, token: str) -> None:
    well = root / ".well-known"
    well.mkdir(exist_ok=True)
    (well / "sentinelai-verify.txt").write_text(
        verify_token_publish_line(token) + "\n", encoding="utf-8"
    )


def run_live_check() -> dict:
    """Run all three scenarios against one local HTTP server."""
    results = {}
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        token = generate_verify_token()
        _write(root, token)

        try:
            handler = partial(_QuietHandler, directory=str(root))
            server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        except OSError as exc:  # pragma: no cover - environment problem
            results["server"] = f"SKIPPED (could not start local server: {exc})"
            return results

        port = server.server_address[1]
        host = f"127.0.0.1:{port}"
        audit = root / "audit.jsonl"
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            # 1. grant - published token matches
            res = verify_domain_ownership(
                host, token, scheme="http", timeout=10.0, audit_path=str(audit)
            )
            results["1_matching_token"] = {
                "host": host,
                "verified": res.verified,
                "reason": res.reason,
                "status_code": res.status_code,
            }
            assert res.verified is True and res.reason == "verified", res

            # 2. deny - token changed on disk -> mismatch
            _write(root, "different-token-published")
            res = verify_domain_ownership(
                host, token, scheme="http", timeout=10.0, audit_path=str(audit)
            )
            results["2_wrong_token"] = {
                "verified": res.verified,
                "reason": res.reason,
                "status_code": res.status_code,
            }
            assert res.verified is False and res.reason == "token_mismatch", res

            # 3. deny - file removed -> 404
            (root / ".well-known" / "sentinelai-verify.txt").unlink()
            res = verify_domain_ownership(
                host, token, scheme="http", timeout=10.0, audit_path=str(audit)
            )
            results["3_missing_file"] = {
                "verified": res.verified,
                "reason": res.reason,
                "status_code": res.status_code,
            }
            assert res.verified is False and res.reason == "file_not_found", res

            # audit trail captured all three (grant + 2 denies)
            with open(audit, encoding="utf-8") as fh:
                records = [json.loads(line) for line in fh if line.strip()]
            results["audit_records"] = len(records)
            assert len(records) == 3, records
            assert [r["decision"] for r in records] == [
                "verified", "denied", "denied",
            ], records
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2.0)
    return results


def test_live_matching_token_grants() -> None:
    res = run_live_check()
    assert res["1_matching_token"]["verified"] is True
    assert res["2_wrong_token"]["verified"] is False
    assert res["3_missing_file"]["verified"] is False


def _main() -> None:
    results = run_live_check()
    for key, value in results.items():
        print(f"  {key}: {json.dumps(value, default=str)}")
    if not results or not results.get("1_matching_token", {}).get("verified"):
        print("LIVE DOMAIN-VERIFY CHECK FAILED")
        raise SystemExit(1)
    print("LIVE DOMAIN-VERIFY CHECK PASSED (3/3 scenarios, 3 audit records)")
    raise SystemExit(0)


if __name__ == "__main__":
    _main()
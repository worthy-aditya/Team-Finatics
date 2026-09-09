"""Day 34 unit tests for sentinelai.active_gate (offline, no network/scan).

Covers the shared two-gate authorization: consent attestation must pass FIRST,
then domain verification, and every other path must FAIL CLOSED with a clear
reason. Also proves --active wiring on both parity-locked CLIs rejects the
unsafe combinations (--active --yes, --active --json). A live end-to-end
check against a real local HTTP server lives in test_active_gate_live.py.
"""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from click.testing import CliRunner

from sentinelai.active_gate import (
    ActiveAuthorization,
    active_scan_host,
    authorize_active_testing,
)
from sentinelai.consent import ConsentError, expected_attestation
from sentinelai.domain_verify import generate_verify_token, verify_token_publish_line

from commands.scan import scan as scan_root
from sentinelai.cli import main as main_cli

TARGET = "https://juice-shop.local"


def _ok_prompt(text, **kwargs):
    """Auto-answer the consent gate with the exact attestation sentence."""
    return expected_attestation(TARGET)


def _fetch_ok(token):
    """Fetch fake that returns the published token line (200)."""
    def fetch(url, timeout):
        return 200, verify_token_publish_line(token)
    return fetch


def _read_log(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def test_authorize_grants_when_both_gates_pass():
    token = generate_verify_token()
    with tempfile.TemporaryDirectory() as td:
        audit = Path(td) / "consent_audit_log.jsonl"
        auth = authorize_active_testing(
            TARGET,
            verify_token=token,
            prompt=_ok_prompt,
            fetch=_fetch_ok(token),
            audit_path=str(audit),
        )
        assert isinstance(auth, ActiveAuthorization)
        assert auth.authorized is True
        assert auth.consent.granted is True
        assert auth.domain is not None and auth.domain.verified is True
        assert auth.blocked_reason == ""
        records = _read_log(audit)
        assert [r["event"] for r in records] == ["consent_attempt", "domain_verify"]
        assert [r["decision"] for r in records] == ["granted", "verified"]


def test_consent_denied_blocks_before_domain_check():
    def deny(text, **kwargs):
        return "quit"

    with tempfile.TemporaryDirectory() as td:
        audit = Path(td) / "a.jsonl"
        auth = authorize_active_testing(
            TARGET, prompt=deny, fetch=_fetch_ok("tok"), audit_path=str(audit)
        )
        assert auth.authorized is False
        assert auth.domain is None
        assert "not granted" in auth.blocked_reason
        records = _read_log(audit)
        assert len(records) == 1 and records[0]["decision"] == "denied"


def test_domain_mismatch_blocks():
    token = generate_verify_token()
    with tempfile.TemporaryDirectory() as td:
        audit = Path(td) / "a.jsonl"
        auth = authorize_active_testing(
            TARGET,
            verify_token=token,
            prompt=_ok_prompt,
            fetch=_fetch_ok("wrong-token-zzz"),
            audit_path=str(audit),
        )
        assert auth.authorized is False
        assert auth.domain is not None and auth.domain.verified is False
        assert "token_mismatch" in auth.blocked_reason


def test_domain_http_404_blocks():
    def fetch404(url, timeout):
        return 404, ""

    with tempfile.TemporaryDirectory() as td:
        audit = Path(td) / "a.jsonl"
        auth = authorize_active_testing(
            TARGET,
            verify_token="tok",
            prompt=_ok_prompt,
            fetch=fetch404,
            audit_path=str(audit),
        )
        assert auth.authorized is False
        assert "file_not_found" in auth.blocked_reason


def test_assume_yes_rejected_before_anything_runs():
    """--yes / assume_yes must raise before consent is even attempted."""
    called = {"prompt": 0}

    def spy_prompt(text, **kwargs):
        called["prompt"] += 1
        return expected_attestation(TARGET)

    with tempfile.TemporaryDirectory() as td:
        audit = Path(td) / "a.jsonl"
        try:
            authorize_active_testing(
                TARGET,
                prompt=spy_prompt,
                fetch=_fetch_ok("tok"),
                assume_yes=True,
                audit_path=str(audit),
            )
        except ConsentError as exc:
            assert "--yes" in str(exc)
        else:
            raise AssertionError("assume_yes must raise ConsentError")
        assert called["prompt"] == 0  # never reached the consent gate
        assert not audit.exists()  # fail-closed: nothing was audited


def test_missing_token_prompts_then_blocks():
    """No --verify-token -> hidden prompt; empty answer -> fail-closed."""

    def empty_hidden(text, **kwargs):
        assert "hide_input" in kwargs  # token prompt must be hidden input
        return ""

    with tempfile.TemporaryDirectory() as td:
        audit = Path(td) / "a.jsonl"
        auth = authorize_active_testing(
            TARGET,
            prompt=_ok_prompt,
            token_prompt=empty_hidden,
            fetch=_fetch_ok("tok"),
            audit_path=str(audit),
        )
        assert auth.authorized is False
        assert auth.domain is None  # fetch never ran without a token
        assert "No verification token" in auth.blocked_reason
        records = _read_log(audit)
        assert [r["decision"] for r in records] == ["granted", "denied"]


def test_active_scan_host_reduces_url_to_hostname():
    assert active_scan_host("http://juice-shop.local:3000/") == "juice-shop.local"
    assert active_scan_host("https://Juice-Shop.LOCAL/app") == "juice-shop.local"
    assert active_scan_host("  127.0.0.1  ") == "127.0.0.1"
    assert active_scan_host("juice-shop.local/") == "juice-shop.local"
    assert active_scan_host("") == ""


def _cli_rejects(command, argv, needle):
    result = CliRunner().invoke(command, argv)
    assert result.exit_code != 0, f"expected failure, got: {result.output}"
    assert needle in result.output


def test_root_cli_rejects_active_yes():
    _cli_rejects(scan_root, ["--target", TARGET, "--active", "--yes"], "--yes")


def test_root_cli_rejects_active_json():
    _cli_rejects(scan_root, ["--target", TARGET, "--active", "--json"], "--json")


def test_package_cli_rejects_active_yes():
    _cli_rejects(main_cli, ["scan", "--target", TARGET, "--active", "--yes"], "--yes")


def test_package_cli_rejects_active_json_file():
    _cli_rejects(
        main_cli,
        ["scan", "--target", TARGET, "--active", "--json-file", "out.json"],
        "--json-file",
    )


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
    print(f"ALL {len(fns) - failures}/{len(fns)} active-gate TESTS PASSED (offline)")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    _main()
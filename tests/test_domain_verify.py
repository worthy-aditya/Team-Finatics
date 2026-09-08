"""Day 33 unit tests for sentinelai.domain_verify (offline, no network).

Covers the token generator, the .well-known publish-line, the tolerant file
parser, URL normalization, and verify_domain_ownership()'s decision matrix
using an injected fake fetcher. The LIVE check against a real local HTTP test
server lives in tests/test_domain_verify_live.py (the Day 33 deliverable).
"""
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sentinelai.domain_verify import (
    DomainVerificationError,
    DomainVerificationResult,
    REASON_FILE_NOT_FOUND,
    REASON_MISMATCH,
    REASON_NO_TOKEN,
    REASON_UNREACHABLE,
    REASON_VERIFIED,
    WELL_KNOWN_PATH,
    extract_verify_token,
    generate_verify_token,
    verification_url,
    verify_domain_ownership,
    verify_token_publish_line,
)

HOST = "juice-shop.local"


def _fake_fetch(status=200, body=None, captures=None):
    """Return a fetch callable; optionally record (url, timeout) calls."""
    calls = [] if captures is None else captures

    def fetch(url, timeout):
        calls.append((url, timeout))
        return status, body or ""

    return fetch


def _read_log(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


# --- token generator -------------------------------------------------------


def test_generate_verify_token_is_long_urlsafe_unique():
    a, b = generate_verify_token(), generate_verify_token()
    assert len(a) >= 30
    assert re.fullmatch(r"[A-Za-z0-9_-]+", a)
    assert a != b


def test_generate_verify_token_short_rejected():
    try:
        generate_verify_token(nbytes=8)
    except DomainVerificationError:
        return
    raise AssertionError("token entropy below 16 bytes should raise")


# --- publish line / parser -------------------------------------------------


def test_publish_line_contains_token():
    tok = generate_verify_token()
    line = verify_token_publish_line(tok)
    assert line == f"sentinelai-verify-token: {tok}"


def test_extract_token_canonical_line():
    tok = generate_verify_token()
    assert extract_verify_token(f"sentinelai-verify-token: {tok}\n") == tok


def test_extract_token_case_and_space_tolerant():
    tok = generate_verify_token()
    assert extract_verify_token(f"  SENTINELAI-VERIFY-TOKEN:{tok}") == tok
    assert extract_verify_token(f"\tSentinelAI-Verify-Token:  {tok}  \n") == tok


def test_extract_token_bare_single_line_fallback():
    tok = generate_verify_token()
    assert extract_verify_token(tok) == tok
    assert extract_verify_token(f"{tok}\n") == tok


def test_extract_token_returns_none_for_junk_or_empty():
    assert extract_verify_token(None) is None
    assert extract_verify_token("") is None
    assert extract_verify_token("garbage with spaces and lines\nsecond line") is None


# --- URL building ----------------------------------------------------------


def test_verification_url_normalizes_hosts():
    assert verification_url(HOST) == f"https://{HOST}/{WELL_KNOWN_PATH}"
    assert verification_url(f"https://{HOST}") == f"https://{HOST}/{WELL_KNOWN_PATH}"
    assert verification_url(f"https://{HOST}/") == f"https://{HOST}/{WELL_KNOWN_PATH}"
    assert verification_url(f"http://127.0.0.1:8080/") == f"http://127.0.0.1:8080/{WELL_KNOWN_PATH}"
    assert verification_url("127.0.0.1:9000") == f"https://127.0.0.1:9000/{WELL_KNOWN_PATH}"


def test_verification_url_preserves_explicit_scheme():
    assert verification_url("http://127.0.0.1:8111").startswith("http://")
    assert verification_url("http://127.0.0.1:8111", scheme="https").startswith("http://")


def test_verification_url_invalid_host_raises():
    try:
        verification_url("   ")
    except DomainVerificationError:
        return
# --- verify_domain_ownership decision matrix -------------------------------


def test_verify_success_and_audit():
    tok = generate_verify_token()
    with tempfile.TemporaryDirectory() as td:
        audit = Path(td) / "consent_audit_log.jsonl"
        calls = []
        fetch = _fake_fetch(200, verify_token_publish_line(tok), captures=calls)
        res = verify_domain_ownership(
            HOST, tok, fetch=fetch, audit_path=str(audit)
        )
        assert isinstance(res, DomainVerificationResult)
        assert res.verified is True
        assert res.reason == REASON_VERIFIED
        assert res.status_code == 200
        assert res.host == HOST
        # fetch used the normalized https URL
        assert calls[0][0] == f"https://{HOST}/{WELL_KNOWN_PATH}"
        lines = _read_log(audit)
        assert len(lines) == 1
        rec = lines[0]
        assert rec["event"] == "domain_verify"
        assert rec["decision"] == "verified"
        assert rec["reason"] == REASON_VERIFIED
        assert rec["status_code"] == 200


def test_verify_denied_on_token_mismatch():
    tok = generate_verify_token()
    with tempfile.TemporaryDirectory() as td:
        audit = Path(td) / "a.jsonl"
        fake = _fake_fetch(200, verify_token_publish_line("other-token-xyz"))
        res = verify_domain_ownership(HOST, tok, fetch=fake, audit_path=str(audit))
        assert res.verified is False
        assert res.reason == REASON_MISMATCH
        rec = _read_log(audit)[0]
        assert rec["decision"] == "denied"
        assert rec["reason"] == REASON_MISMATCH


def test_verify_file_not_found_on_404():
    fake = _fake_fetch(404, "")
    with tempfile.TemporaryDirectory() as td:
        audit = Path(td) / "a.jsonl"
        res = verify_domain_ownership(HOST, "tok", fetch=fake, audit_path=str(audit))
        assert res.verified is False
        assert res.reason == REASON_FILE_NOT_FOUND
        assert res.status_code == 404


def test_verify_no_token_when_file_is_junk():
    fake = _fake_fetch(200, "just some random homepage html")
    res = verify_domain_ownership(HOST, "tok", fetch=fake, audit_path=None)
    assert res.verified is False
    assert res.reason == REASON_NO_TOKEN


def test_verify_unreachable_denied_and_audited():
    def boom(url, timeout):
        raise ConnectionError("connection refused")

    with tempfile.TemporaryDirectory() as td:
        audit = Path(td) / "a.jsonl"
        res = verify_domain_ownership(HOST, "tok", fetch=boom, audit_path=str(audit))
        assert res.verified is False
        assert res.reason == REASON_UNREACHABLE
        assert res.status_code is None
        rec = _read_log(audit)[0]
        assert rec["decision"] == "denied"
        assert rec["reason"] == REASON_UNREACHABLE


def test_verify_scheme_http_for_local_lab():
    tok = generate_verify_token()
    calls = []
    fetch = _fake_fetch(200, verify_token_publish_line(tok), captures=calls)
    res = verify_domain_ownership(
        "127.0.0.1:8888", tok, scheme="http", fetch=fetch, audit_path=None
    )
    assert res.verified is True
    assert calls[0][0] == f"http://127.0.0.1:8888/{WELL_KNOWN_PATH}"


def test_verify_invalid_input_raises():
    for bad_host, bad_token in [("  ", "tok"), (HOST, "  "), ("", "")]:
        try:
            verify_domain_ownership(bad_host, bad_token, fetch=_fake_fetch())
        except DomainVerificationError:
            continue
        raise AssertionError(f"expected DomainVerificationError for {bad_host!r}/{bad_token!r}")


def test_audit_disabled_no_crash():
    tok = generate_verify_token()
    res = verify_domain_ownership(
        HOST, tok, fetch=_fake_fetch(200, verify_token_publish_line(tok)), audit_path=None
    )
    assert res.verified is True


def _main():
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
    print(f"ALL {len(fns) - failures}/{len(fns)} domain_verify TESTS PASSED (offline)")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    _main()
    raise AssertionError("empty host should raise DomainVerificationError")
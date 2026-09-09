"""Day 32 unit tests for sentinelai.consent (offline, pure functions).

Covers the typed-attestation flow: exact match grants, mismatches deny (with
bounded retries), quit/Ctrl+C cancel safely, every attempt is appended to
consent_audit_log.jsonl, and assume_yes is rejected. No network is required.
"""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sentinelai.consent import (
    ATTESTATION_TEMPLATE,
    ConsentError,
    ConsentResult,
    request_consent,
    _normalize,
    expected_attestation,
)

TARGET = "https://juice-shop.local"


def _seq_prompt(*answers):
    """Injected prompt callable; returns answers in order then the last one."""
    answers = list(answers) or [""]

    def _prompt(text, **kwargs):
        return answers.pop(0) if len(answers) > 1 else answers[0]

    return _prompt


def _read_log(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def test_exact_match_granted():
    with tempfile.TemporaryDirectory() as td:
        audit = Path(td) / "consent_audit_log.jsonl"
        phrase = expected_attestation(TARGET)
        res = request_consent(TARGET, audit_path=str(audit), prompt=_seq_prompt(phrase))

        assert isinstance(res, ConsentResult)
        assert res.granted is True
        assert res.reason == "attestation_match"
        assert res.attempts == 1

        lines = _read_log(audit)
        assert len(lines) == 1
        rec = lines[0]
        assert rec["event"] == "consent_attempt"
        assert rec["decision"] == "granted"
        assert rec["reason"] == "attestation_match"
        assert rec["target"] == TARGET
        assert {"timestamp", "typed_length", "user", "host", "version"} <= set(rec)


def test_quotes_and_case_and_space_variance_accepted():
    with tempfile.TemporaryDirectory() as td:
        audit = Path(td) / "a.jsonl"
        # User includes quotes, mixed case, and extra whitespace: still matches.
        typed = '  "' + ATTESTATION_TEMPLATE.format(target=TARGET).upper() + '"  '
        res = request_consent(TARGET, audit_path=str(audit), prompt=_seq_prompt(typed))
        assert res.granted is True
        assert res.reason == "attestation_match"


def test_mismatch_denies_and_logs_every_attempt():
    with tempfile.TemporaryDirectory() as td:
        audit = Path(td) / "a.jsonl"
        prompt = _seq_prompt("I do not own this", "Slight typo in phrase", "nope")
        res = request_consent(TARGET, audit_path=str(audit), prompt=prompt, max_attempts=3)

        assert res.granted is False
        assert res.reason == "attestation_mismatch"
        lines = _read_log(audit)
        assert len(lines) == 3  # every attempt recorded
        assert all(l["decision"] == "denied" and l["reason"] == "attestation_mismatch" for l in lines)


def test_retry_then_granted_records_both():
    with tempfile.TemporaryDirectory() as td:
        audit = Path(td) / "a.jsonl"
        prompt = _seq_prompt("Wrong word", expected_attestation(TARGET))
        res = request_consent(TARGET, audit_path=str(audit), prompt=prompt, max_attempts=3)

        assert res.granted is True
        assert res.attempts == 2
        lines = _read_log(audit)
        assert len(lines) == 2
        assert lines[0]["decision"] == "denied"
        assert lines[1]["decision"] == "granted"
        assert lines[1]["reason"] == "attestation_match"


def test_quit_cancels_and_is_logged():
    with tempfile.TemporaryDirectory() as td:
        audit = Path(td) / "a.jsonl"
        res = request_consent(TARGET, audit_path=str(audit), prompt=_seq_prompt("quit"))
        assert res.granted is False
        assert res.reason == "user_cancel"
        lines = _read_log(audit)
        assert len(lines) == 1
        assert lines[0]["decision"] == "denied"
        assert lines[0]["reason"] == "user_cancel"


def test_ctrl_c_aborts_denied():
    def interrupt(text, **kwargs):
        raise KeyboardInterrupt()

    with tempfile.TemporaryDirectory() as td:
        audit = Path(td) / "a.jsonl"
        res = request_consent(TARGET, audit_path=str(audit), prompt=interrupt)
        assert res.granted is False
        assert res.reason == "aborted"
        lines = _read_log(audit)
        assert len(lines) == 1
        assert lines[0]["decision"] == "denied"
        assert lines[0]["reason"] == "aborted"


def test_blank_input_counts_as_mismatch():
    with tempfile.TemporaryDirectory() as td:
        audit = Path(td) / "a.jsonl"
        prompt = _seq_prompt("   ", "   ")
        res = request_consent(TARGET, audit_path=str(audit), prompt=prompt, max_attempts=2)
        assert res.granted is False
        assert res.reason == "attestation_mismatch"


def test_empty_target_raises():
    try:
        request_consent("   ", prompt=_seq_prompt("x"))
    except ConsentError:
        return
    raise AssertionError("empty target should raise ConsentError")


def test_assume_yes_rejected():
    try:
        request_consent(TARGET, assume_yes=True, prompt=_seq_prompt("x"))
    except ConsentError as exc:
        assert "cannot be approved with --yes" in str(exc)
        return
    raise AssertionError("assume_yes must be rejected for active testing")


def test_audit_optional_no_crash():
    res = request_consent(TARGET, audit_path=None, prompt=_seq_prompt(expected_attestation(TARGET)))
    assert res.granted is True


def test_normalize():
    assert _normalize('  "  Hi  There  "  ') == "hi there"
    assert _normalize("  '  one   two  ' ") == "one two"
    assert _normalize("no quotes   here") == "no quotes here"


def test_expected_attestation_embeds_target():
    assert TARGET in expected_attestation(TARGET)
    assert expected_attestation(TARGET).startswith("i authorize active security testing of")


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
    print(f"ALL {len(fns) - failures}/{len(fns)} consent TESTS PASSED (offline)")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    _main()
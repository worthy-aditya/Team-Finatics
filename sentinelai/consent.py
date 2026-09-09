"""Consent gate for active security testing (Feature Sprint, Day 32).

Implements the typed-attestation front half of the two-layer authorization
system designed on Day 31. ``request_consent()`` asks an operator to type an
exact attestation sentence about a target, retries a bounded number of times,
and appends a JSONL audit record for *every* attempt (granted or denied) to
``consent_audit_log.jsonl``.

Design rules carried forward from the Feature-Sprint plan (Days 31-32):
- ``request_consent`` NEVER auto-approves. Active testing has no ``--yes`` /
  ``assume_yes`` path (unlike the passive Day 20 ``request_approval`` flow).
- Matching is strict by design: normalized case + whitespace only. Typos in
  words fail; a mismatch is denied.
- The audit log is written *before* a grant returns (fail-closed: a
  granted-but-unlogged run must be impossible).
- Only the audit trail + domain verification are provided by this gate; it
  does not and cannot verify legal authorization.
"""

from __future__ import annotations

import json
import os
import platform
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional

import click

from sentinelai.ui import error, print_panel, warn

__all__ = [
    "ConsentError",
    "ConsentResult",
    "DEFAULT_AUDIT_PATH",
    "expected_attestation",
    "request_consent",
]

# Version stamped into audit records (kept in sync with sentinelai.py).
VERSION = "1.0.0"

# The attestation sentence. {target} is interpolated at call time. The CLI
# shows this (without the placeholders) and requires it typed back.
ATTESTATION_TEMPLATE = (
    "I authorize active security testing of {target} and confirm that I own "
    "this system or have written authorization to test it."
)

# Short answers that always cancel (checked before phrase matching).
_CANCEL_WORDS = {"quit", "q", "cancel", "abort", "no"}

DEFAULT_AUDIT_PATH = "consent_audit_log.jsonl"

# Reason tags recorded in the audit log (Day 31 schema).
REASON_MATCH = "attestation_match"
REASON_MISMATCH = "attestation_mismatch"
REASON_CANCEL = "user_cancel"
REASON_ABORTED = "aborted"


class ConsentError(ValueError):
    """Raised when the consent workflow cannot run safely.

    Mirrors ``sentinelai.approval.ApprovalError`` so both gates share one
    error-handling surface in the CLI.
    """


@dataclass(frozen=True)
class ConsentResult:
    """Outcome of one consent attempt (granted/denied + audit reason)."""

    granted: bool
    reason: str
    target: str
    timestamp: str
    typed: str = ""
    attempts: int = 0


def _normalize(text: str) -> str:
    """Strip one pair of surrounding quotes, collapse whitespace, lowercase.

    Normalization is deliberately minimal: quotes may be omitted or included;
    spacing/case may vary slightly; *words* must be exact. This lets a real
    operator copy-paste the sentence while still catching genuinely different
    text.
    """
    text = text.strip()
    if len(text) >= 2 and text[0] in ("'", '"') and text[-1] == text[0]:
        text = text[1:-1]
    return re.sub(r"\s+", " ", text).strip().lower()


def expected_attestation(target: str) -> str:
    """Build the exact (normalized) attestation sentence for ``target``."""
    if not target or not target.strip():
        raise ConsentError("A target is required before asking for consent.")
    return _normalize(ATTESTATION_TEMPLATE.format(target=target))


def _panel_text(target: str) -> str:
    """Human-readable explanation shown before the first prompt."""
    phrase = ATTESTATION_TEMPLATE.format(target=target)
    return (
        f"Target    : {target}\n"
        f"Engine    : OWASP ZAP active scan (sends real attack traffic)\n"
        f"\n"
        f"Active scans can alter, damage, or crash the target application, "
        f"trigger WAF/IDS alerts on the hosting network, and carry legal "
        f"consequences if you do not own the target.\n"
        f"\n"
        "SentinelAI requires TWO confirmations before any active request:\n"
        "  1. ATTESTATION - confirm you own the target or have written\n"
        "     authorization to test it (this prompt).\n"
        "  2. DOMAIN VERIFICATION - a token file the target's administrator\n"
        f"     publishes at https://<host>/.well-known/sentinelai-verify.txt\n"
        f"\n"
        f"Type EXACTLY (quotes optional):\n"
        f"  {phrase}\n"
        f"\n"
        "Your exact response and decision are recorded in the local audit "
        "log. SentinelAI verifies domain control only; it does not and "
        "cannot verify legal authorization. You remain responsible."
    )


def _audit_record(
    target: str,
    decision: str,
    reason: str,
    typed: str,
    *,
    user: Optional[str] = None,
    host: Optional[str] = None,
) -> dict:
    try:
        user = user or os.getenv("USERNAME") or os.getenv("USER") or "unknown"
        host = host or platform.node() or "unknown"
    except Exception:  # pragma: no cover - getenv/node are safe; belt & braces
        user = user or "unknown"
        host = host or "unknown"
    return {
        "timestamp": datetime.now().isoformat(),
        "event": "consent_attempt",
        "target": target,
        "decision": decision,
        "reason": reason,
        "typed_length": len(typed or ""),
        "user": user,
        "host": host,
        "version": VERSION,
    }


def _append_audit(audit_path: Optional[str], record: dict) -> None:
    """Append one JSON line to the audit log (fail-closed on I/O errors)."""
    if not audit_path:
        return
    try:
        with open(audit_path, "a", encoding="utf-8") as audit_file:
            audit_file.write(json.dumps(record) + "\n")
    except OSError as exc:  # fail-closed: no silent loss of the trail
        raise ConsentError(
            f"Could not write consent audit log ({audit_path!r}): {exc}. "
            "Denying consent; no active testing can proceed."
        ) from exc
def request_consent(
    target: str,
    *,
    audit_path: Optional[str] = DEFAULT_AUDIT_PATH,
    prompt: Callable[..., str] = click.prompt,
    max_attempts: int = 3,
    assume_yes: bool = False,
) -> ConsentResult:
    """Ask an operator to type the exact attestation sentence for ``target``.

    Parameters
    ----------
    target
        The exact target string the operator intends to test.
    audit_path
        JSONL file to append every attempt to. Set to ``None`` to disable
        logging (not recommended; default logs to ``consent_audit_log.jsonl``).
    prompt
        Callable used to read the typed sentence. Injected in unit tests;
        defaults to :func:`click.prompt`.
    max_attempts
        How many times a phrase may be typed before the gate denies.
    assume_yes
        MUST stay False for active testing. If True, the gate refuses to run
        with an explanatory error (no auto-approve path exists).

    Returns
    -------
    ConsentResult
        ``granted`` is True only when the operator typed the exact sentence.
    """
    if assume_yes:
        raise ConsentError(
            "Active testing cannot be approved with --yes / assume_yes. "
            "You must type the attestation sentence verbatim."
        )

    if not target or not target.strip():
        raise ConsentError("A valid target is required for consent.")

    expected = expected_attestation(target)

    print_panel(
        _panel_text(target),
        title="\u26a0\ufe0f ACTIVE TESTING \u2014 AUTHORIZATION REQUIRED",
        border_style="red",
    )

    timestamp0 = datetime.now().isoformat()
    for attempt in range(1, max_attempts + 1):
        try:
            typed = prompt(
                "Type the attestation sentence to confirm, or type 'quit'. "
                f"(attempt {attempt}/{max_attempts})",
                hide_input=False,
            )
        except (KeyboardInterrupt, click.Abort, EOFError):
            # Ctrl+C / EOF must never let the scan run.
            record = _audit_record(target, "denied", REASON_ABORTED, "")
            _append_audit(audit_path, record)
            error("Consent aborted - no active testing will run.")
            return ConsentResult(False, REASON_ABORTED, target, timestamp0, "", attempt)

        typed = (typed or "").strip()
        low = typed.lower()

        # Short cancel words always cancel, unless they ARE the attestation.
        if low in _CANCEL_WORDS:
            record = _audit_record(target, "denied", REASON_CANCEL, typed)
            _append_audit(audit_path, record)
            warn("Consent denied - active testing cancelled by operator.")
            return ConsentResult(False, REASON_CANCEL, target, timestamp0, typed, attempt)

        if _normalize(typed) == expected:
            record = _audit_record(target, "granted", REASON_MATCH, typed)
            _append_audit(audit_path, record)
            return ConsentResult(True, REASON_MATCH, target, timestamp0, typed, attempt)

        # Mismatch - log this attempt and retry (if attempts remain).
        record = _audit_record(target, "denied", REASON_MISMATCH, typed)
        _append_audit(audit_path, record)
        if attempt < max_attempts:
            warn(
                "Attestation did not match. "
                f"{max_attempts - attempt} attempt(s) remaining."
            )

    error(
        "Consent denied - the exact attestation was not typed after "
        f"{max_attempts} attempts."
    )
    return ConsentResult(False, REASON_MISMATCH, target, timestamp0, "", max_attempts)
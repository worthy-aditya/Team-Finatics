"""Domain verification for active security testing (Feature Sprint, Day 33).

Second layer of the two-layer authorization system designed on Day 31. After
the typed-attestation consent gate (``sentinelai/consent.py``, Day 32), active
testing must ALSO prove the target's real administrator consents by publishing
a token file at:

    https://<host>/.well-known/sentinelai-verify.txt

This module provides everything needed for that check (Day 33 deliverable):

- ``generate_verify_token()``        - cryptographically random URL-safe token
- ``verify_token_publish_line()``    - the exact line an admin places in the file
- ``extract_verify_token()``         - tolerant parser of the file's content
- ``verification_url()``             - normalizes any user-supplied host string
- ``verify_domain_ownership()``      - fetches the file, compares the token, and
                                      appends an audit record (grant or deny)

Security notes (carried from the Feature-Sprint plan):
- ``verify_domain_ownership`` NEVER trusts a single string: it fetches the
  published file over the network and compares tokens (default scheme https).
- It proves *domain control*, not legal authorization; the audit trail keeps
  every grant/deny accountable.
- Like the consent gate, there is no ``assume_yes`` path here.
- The default fetcher is injectable so unit tests never touch the network.
"""

from __future__ import annotations

import json
import os
import platform
import re
import secrets
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, urlunparse
from urllib.request import Request, urlopen

__all__ = [
    "DomainVerificationError",
    "DomainVerificationResult",
    "DEFAULT_AUDIT_PATH",
    "WELL_KNOWN_PATH",
    "extract_verify_token",
    "generate_verify_token",
    "verification_url",
    "verify_domain_ownership",
    "verify_token_publish_line",
]

# Version stamped into audit records (kept in sync with sentinelai.py).
VERSION = "1.0.0"

# Where the admin publishes the token (relative to the origin).
WELL_KNOWN_PATH = ".well-known/sentinelai-verify.txt"

# Shared audit log (same file as the consent gate -> one unified trail).
DEFAULT_AUDIT_PATH = "consent_audit_log.jsonl"

# Result reason tags recorded in the audit log (Day 31 schema family).
REASON_VERIFIED = "verified"
REASON_FILE_NOT_FOUND = "file_not_found"
REASON_NO_TOKEN = "no_token_found"
REASON_MISMATCH = "token_mismatch"
REASON_UNREACHABLE = "unreachable"


class DomainVerificationError(ValueError):
    """Raised when the verification workflow cannot run safely.

    Mirrors ``sentinelai.consent.ConsentError`` / ``ApprovalError`` so the
    whole authorization layer shares one error surface in the CLI (Day 34).
    """


@dataclass(frozen=True)
class DomainVerificationResult:
    """Outcome of one domain-verification attempt."""

    verified: bool
    host: str
    reason: str
    timestamp: str
    status_code: Optional[int] = None
    url: str = ""


def generate_verify_token(nbytes: int = 32) -> str:
    """Generate a cryptographically random, URL-safe verification token.

    The token is what an administrator publishes in ``.well-known/
    sentinelai-verify.txt`` to prove they control the domain. 32 bytes of
    entropy (about 43 URL-safe chars) is comfortably above brute-force reach.
    """
    if nbytes < 16:
        raise DomainVerificationError(
            "Verification token entropy must be >= 16 bytes (got %d)." % nbytes
        )
    return secrets.token_urlsafe(nbytes)


def verify_token_publish_line(token: str) -> str:
    """Return the exact line to place in ``.well-known/sentinelai-verify.txt``.

    The parser is deliberately tolerant (see ``extract_verify_token``), but
    publishing THIS canonical form is what the Day 34 CLI instructions will
    recommend.
    """
    if not token or not token.strip():
        raise DomainVerificationError(
            "A token is required before it can be published."
        )
    return f"sentinelai-verify-token: {token.strip()}"


def extract_verify_token(content: Optional[str]) -> Optional[str]:
    """Extract the published token from a ``.well-known`` file's text.

    Accepts the canonical ``sentinelai-verify-token: <tok>`` line (case- and
    whitespace-insensitive) OR a bare single-token file. Returns ``None`` when
    no usable token is found, so callers can audit a clean "no_token_found".
    """
    if not content:
        return None
    for raw_line in content.splitlines():
        line = raw_line.strip()
        match = re.match(
            r"^sentinelai-verify-token\s*:\s*(\S+)\s*$", line, re.IGNORECASE
        )
        if match:
            return match.group(1)
    # Fallback: the whole file is exactly one clean token with no whitespace.
    stripped = content.strip()
    if stripped and "\n" not in stripped and " " not in stripped:
        return stripped
def verification_url(host: str, scheme: str = "https") -> str:
    """Build the ``.well-known`` verification URL for a user-supplied host.

    ``host`` may be any of ``"juice-shop.local"``, ``"https://juice-shop.local"``,
    ``"juice-shop.local:8443"``, or ``"http://127.0.0.1:8000/"``. It is
    normalized to a single origin + the well-known path. Bare hosts default to
    ``scheme`` (https); an explicit scheme in the host string is preserved (so
    local-lab http servers remain testable).
    """
    if not host or not host.strip():
        raise DomainVerificationError(
            "A target host is required before verifying domain ownership."
        )
    raw = host.strip().rstrip("/")
    if "://" in raw:
        parsed = urlparse(raw)
        netloc = parsed.netloc or parsed.path
        use_scheme = parsed.scheme or scheme
    else:
        netloc = raw
        use_scheme = scheme
    if not netloc:
        raise DomainVerificationError(f"Could not parse a host from {host!r}.")
    return urlunparse((use_scheme, netloc, "/" + WELL_KNOWN_PATH, "", "", ""))


def _default_fetch(url: str, timeout: float) -> Tuple[int, str]:
    """Default fetcher: GET ``url`` and return ``(status_code, body_text)``.

    Uses only the stdlib (``urllib``) so no extra dependency is added.
    ``urllib`` raises ``HTTPError`` for 4xx/5xx responses (it does not return
    a response object), so those are converted into a status code + empty
    body; genuine connection-level failures (DNS, refused, timeout) propagate
    so the caller maps them to an ``unreachable`` result. (Found by the Day 33
    live-test against a real local server.)
    """
    request = Request(url, headers={"User-Agent": "SentinelAI/" + VERSION})
    try:
        with urlopen(request, timeout=timeout) as response:
            status = getattr(response, "status", 200)
            return status, response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        # The request worked but the server answered with an error (e.g. 404).
        return exc.code, ""
    except URLError:
        # Connection-level failure -> 'unreachable' in the caller.
        raise


def _audit_record(
    host: str,
    decision: str,
    reason: str,
    *,
    status_code: Optional[int] = None,
    url: str = "",
    user: Optional[str] = None,
    machine: Optional[str] = None,
) -> dict:
    try:
        user = user or os.getenv("USERNAME") or os.getenv("USER") or "unknown"
        machine = machine or platform.node() or "unknown"
    except Exception:  # pragma: no cover - getenv/node are safe; belt & braces
        user = user or "unknown"
        machine = machine or "unknown"
    return {
        "timestamp": datetime.now().isoformat(),
        "event": "domain_verify",
        "target": host,
        "url": url,
        "decision": decision,
        "reason": reason,
        "status_code": status_code,
        "user": user,
        "host": machine,
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
        raise DomainVerificationError(
            f"Could not write audit log ({audit_path!r}): {exc}. "
            "Denying verification; no active testing can proceed."
        ) from exc
def verify_domain_ownership(
    host: str,
    expected_token: str,
    *,
    scheme: str = "https",
    timeout: float = 10.0,
    fetch: Callable[[str, float], Tuple[int, str]] = _default_fetch,
    audit_path: Optional[str] = DEFAULT_AUDIT_PATH,
) -> DomainVerificationResult:
    """Verify that ``host``'s administrator publishes ``expected_token``.

    The file at ``https://<host>/.well-known/sentinelai-verify.txt`` is
    fetched (default scheme https) and its token compared to
    ``expected_token``. Every outcome is appended to the audit log.

    Parameters
    ----------
    host
        Target host: bare hostname/IP, with optional scheme/port/path.
    expected_token
        Token the administrator should have published. Generate one with
        :func:`generate_verify_token`.
    scheme
        Default scheme for bare hosts (https for real use; http permitted for
        local-lab testing only).
    timeout
        Seconds to wait for the fetch.
    fetch
        Injected fetch callable ``(url, timeout) -> (status_code, body)``.
        Defaults to a stdlib urllib GET. Tests pass a fake so no network is
        used.
    audit_path
        JSONL file to append every attempt to (defaults to the consent
        audit log so one file holds the whole authorization trail).

    Returns
    -------
    DomainVerificationResult
        ``verified`` is True only when the published token matches exactly.
    """
    if not host or not host.strip():
        raise DomainVerificationError(
            "A valid target host is required for domain verification."
        )
    if not expected_token or not expected_token.strip():
        raise DomainVerificationError(
            "A verification token is required; run generate_verify_token()."
        )

    url = verification_url(host, scheme=scheme)
    expected = expected_token.strip()
    timestamp = datetime.now().isoformat()

    try:
        status, body = fetch(url, timeout)
    except Exception:  # noqa: BLE001 - any transport failure is 'unreachable'
        _append_audit(
            audit_path,
            _audit_record(host, "denied", REASON_UNREACHABLE, url=url),
        )
        return DomainVerificationResult(
            False, host, REASON_UNREACHABLE, timestamp, None, url
        )

    if status == 404:
        reason = REASON_FILE_NOT_FOUND
    else:
        published = extract_verify_token(body)
        if published is None:
            reason = REASON_NO_TOKEN
        elif published != expected:
            reason = REASON_MISMATCH
        else:
            reason = REASON_VERIFIED

    verified = reason == REASON_VERIFIED
    _append_audit(
        audit_path,
        _audit_record(
            host,
            "verified" if verified else "denied",
            reason,
            status_code=status,
            url=url,
        ),
    )
    return DomainVerificationResult(
        verified, host, reason, timestamp, status, url
    )
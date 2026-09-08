"""Active-testing authorization gate (Feature Sprint, Day 34).

Wires the two-layer authorization system into ONE function that both CLI
entry points call behind the ``--active`` flag:

    --active blocks until BOTH authorization checks pass:

      1. consent gate       request_consent(target)          (Day 32)
      2. domain verification verify_domain_ownership(target) (Day 33)

A single shared implementation keeps the two parity-locked CLIs identical
(see tests/test_cli_sync.py) and gives the Day 34 deliverable one place to
be tested offline. It is intentionally minimal: no scan/network logic beyond
the two gates, no ZAP code (that is Affan's track, Days 36/38-40).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional
from urllib.parse import urlparse

import click

from sentinelai.consent import DEFAULT_AUDIT_PATH, ConsentError, ConsentResult, request_consent
from sentinelai.domain_verify import (
    REASON_NO_TOKEN_PROVIDED,
    _append_audit,
    _audit_record,
    _default_fetch,
    DomainVerificationResult,
    verify_domain_ownership,
)

__all__ = [
    "ActiveAuthorization",
    "active_scan_host",
    "authorize_active_testing",
]


@dataclass(frozen=True)
class ActiveAuthorization:
    """Outcome of running both gates (consent then domain verification)."""

    authorized: bool
    consent: ConsentResult
    domain: Optional[DomainVerificationResult] = None
    blocked_reason: str = ""


def active_scan_host(target: str) -> str:
    """Extract an nmap-scan-able host from an optional URL-like target.

    ``--active`` targets are sites (e.g. ``http://juice-shop.local``), but the
    scan stage still needs a plain host for nmap. A bare host is returned
    unchanged; a URL is reduced to its hostname (port stays a ZAP concern).
    """
    target = (target or "").strip()
    if "://" in target:
        host = urlparse(target).hostname
        if host:
            return host
    return target.rstrip("/")


def authorize_active_testing(
    target: str,
    *,
    verify_token: Optional[str] = None,
    scheme: str = "https",
    timeout: float = 10.0,
    audit_path: Optional[str] = DEFAULT_AUDIT_PATH,
    prompt: Callable[..., str] = click.prompt,
    token_prompt: Callable[..., str] = click.prompt,
    assume_yes: bool = False,
    fetch: Optional[Callable] = None,
) -> ActiveAuthorization:
    """Run consent gate then domain verification for ``target``.

    Parameters
    ----------
    target
        The exact site string the operator intends to actively test
        (bare host or URL).
    verify_token
        Token the administrator published at
        ``.well-known/sentinelai-verify.txt``. When omitted, it is prompted
        for (hidden input).
    scheme
        Default scheme for the domain-verification fetch (https; http only
        for local-lab targets that pass an explicit ``http://`` target).
    timeout
        Seconds to wait for the verification fetch.
    audit_path
        Shared JSONL audit log (same as consent + domain gates).
    prompt / token_prompt
        Injected input callables (unit tests never touch the network/UI).
    assume_yes
        MUST stay False: active testing cannot be auto-approved.
    fetch
        Injected fetcher for ``verify_domain_ownership`` (tests). Defaults to
        the real urllib GET.

    Returns
    -------
    ActiveAuthorization
        ``authorized`` is True only when BOTH gates pass. Fails-closed on
        every other path, with a ``blocked_reason`` ready for the CLI.
    """
    if assume_yes:
        raise ConsentError(
            "Active testing cannot be approved with --yes / assume_yes. "
            "You must type the attestation sentence verbatim."
        )

    consent = request_consent(target, audit_path=audit_path, prompt=prompt)
    if not consent.granted:
        return ActiveAuthorization(
            False,
            consent,
            None,
            f"Consent attestation was not granted (reason: {consent.reason}).",
        )

    token = (verify_token or "").strip()
    if not token:
        try:
            token = (
                token_prompt(
                    "Paste the verification token published at "
                    ".well-known/sentinelai-verify.txt",
                    hide_input=True,
                )
                or ""
            ).strip()
        except (KeyboardInterrupt, click.Abort, EOFError):
            token = ""
    if not token:
        _append_audit(
            audit_path,
            _audit_record(target, "denied", REASON_NO_TOKEN_PROVIDED, url=""),
        )
        return ActiveAuthorization(
            False,
            consent,
            None,
            "No verification token was provided. Generate one with "
            "generate_verify_token(), publish it, then retry with "
            "--verify-token.",
        )

    domain = verify_domain_ownership(
        target,
        token,
        scheme=scheme,
        timeout=timeout,
        fetch=fetch if fetch is not None else _default_fetch,
        audit_path=audit_path,
    )
    if not domain.verified:
        return ActiveAuthorization(
            False,
            consent,
            domain,
            f"Domain verification failed: {domain.reason} "
            f"(status={domain.status_code}, url={domain.url}).",
        )
    return ActiveAuthorization(True, consent, domain)
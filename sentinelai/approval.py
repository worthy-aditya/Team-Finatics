"""Human approval workflow for operations initiated by SentinelAI."""

import json
from datetime import datetime
from typing import Callable, Optional

import click


class ApprovalError(ValueError):
    """Raised when an operation cannot safely enter the approval workflow."""


def validate_operation(action: str, target: str) -> None:
    """Validate the minimum information needed before asking for approval."""
    if not action or not action.strip():
        raise ApprovalError("An operation name is required")
    if not target or not target.strip():
        raise ApprovalError("A target is required")


def request_approval(
    action: str,
    target: str,
    *,
    assume_yes: bool = False,
    confirm: Callable[..., bool] = click.confirm,
    audit_path: Optional[str] = None,
) -> bool:
    """Ask for approval before an operation can execute.

    ``assume_yes`` is intended for explicitly opted-in automation. It does not
    skip validation, and the default path always requires interactive consent.
    """
    validate_operation(action, target)
    if assume_yes:
        approved = True
    else:
        approved = confirm(
            f"Approve {action} on {target}?",
            default=False,
            abort=False,
        )

    if audit_path:
        with open(audit_path, "a", encoding="utf-8") as audit_file:
            audit_file.write(json.dumps({
                "timestamp": datetime.now().isoformat(),
                "action": action,
                "target": target,
                "approved": approved,
            }) + "\n")

    return approved
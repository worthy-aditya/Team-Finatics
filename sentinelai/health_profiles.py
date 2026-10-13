"""sentinelai/health_profiles.py - Day 57 (Week 9).

Provider health profiles.

Week 8 built the provider-health engine: scores drive routing (Day 52), the
dashboard (Day 53), history/trends (Day 54), alerts (Day 55), and health-gated
selection (Day 56). Those scores were always supplied ad hoc via a
``--provider-scores`` JSON file. Day 57 opens Week 9 by making provider health
**reproducible**: a profile is a named, saved set of provider health scores that
can be listed, loaded, and deleted from disk, then fed straight into the rest of
the pipeline.

Use cases: capture a "known-good" baseline for CI/regression, a "degraded" state
for exercising the alert/quarantine paths, or a demo state for presentations -
all without touching a live provider.

All functions are pure Python and offline: no LLM or network calls.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

# Directory (relative to the repo root) where profiles are stored. Only written
# when a caller explicitly saves a profile - never as an import side effect.
DEFAULT_PROFILES_DIR = "provider_profiles"

# Profile names are restricted to this set so a name can never escape the
# profiles directory (no path separators, no traversal) or collide with the
# ".json" suffix handling.
_SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


def _validate_name(name: str) -> str:
    """Return a sanitized profile name or raise ValueError.

    Rejects empty names, names with path separators / traversal, and names that
    are not simple identifiers so ``save_profile`` can never write outside the
    profiles directory.
    """
    if not isinstance(name, str) or not _SAFE_NAME.match(name):
        raise ValueError(
            f"Invalid profile name {name!r}: use letters, digits, '-' or '_' "
            "(must start with a letter or digit)."
        )
    return name


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def profile_path(name: str, profiles_dir: Optional[str] = None) -> Path:
    """Return the on-disk path for a named profile (does not create it)."""
    safe = _validate_name(name)
    base = Path(profiles_dir or DEFAULT_PROFILES_DIR)
    return base / f"{safe}.json"


def save_profile(
    name: str,
    scores: Dict[str, float],
    profiles_dir: Optional[str] = None,
) -> Path:
    """Persist a named provider-health profile and return its path.

    ``scores`` maps provider name -> health score (0-100). The stored document
    also records the profile name and a UTC ``saved_at`` timestamp. Overwrites an
    existing profile of the same name. Raises ValueError for an invalid name or
    empty/invalid scores.
    """
    safe = _validate_name(name)
    if not scores or not isinstance(scores, dict):
        raise ValueError("scores must be a non-empty {provider: score} mapping")

    normalized: Dict[str, float] = {}
    for provider, score in scores.items():
        key = str(provider)
        try:
            normalized[key] = float(score)
        except (TypeError, ValueError):
            raise ValueError(f"score for {key!r} is not a number: {score!r}")

    target = profile_path(safe, profiles_dir)
    target.parent.mkdir(parents=True, exist_ok=True)
    document = {
        "name": safe,
        "saved_at": _now_iso(),
        "scores": normalized,
    }
    target.write_text(json.dumps(document, indent=2), encoding="utf-8")
    return target


def load_profile(
    name: str,
    profiles_dir: Optional[str] = None,
) -> Dict[str, float]:
    """Load and return the ``{provider: score}`` map for a named profile.

    Raises FileNotFoundError if the profile does not exist, and ValueError if
    the stored document is malformed.
    """
    safe = _validate_name(name)
    target = profile_path(safe, profiles_dir)
    if not target.exists():
        raise FileNotFoundError(f"No provider health profile named {safe!r}")
    try:
        document = json.loads(target.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise ValueError(f"Profile {safe!r} is corrupt: {exc}")
    scores = document.get("scores") if isinstance(document, dict) else None
    if not isinstance(scores, dict) or not scores:
        raise ValueError(f"Profile {safe!r} has no valid scores")
    return {str(k): float(v) for k, v in scores.items()}


def profile_exists(name: str, profiles_dir: Optional[str] = None) -> bool:
    """Return True when a named profile exists on disk."""
    try:
        return profile_path(name, profiles_dir).exists()
    except ValueError:
        return False


def list_profiles(profiles_dir: Optional[str] = None) -> List[str]:
    """Return the sorted names of all saved profiles (without the .json suffix)."""
    base = Path(profiles_dir or DEFAULT_PROFILES_DIR)
    if not base.exists():
        return []
    return sorted(p.stem for p in base.glob("*.json") if p.is_file())


def delete_profile(name: str, profiles_dir: Optional[str] = None) -> bool:
    """Delete a named profile. Returns True if a file was removed, else False."""
    safe = _validate_name(name)
    target = profile_path(safe, profiles_dir)
    if target.exists():
        target.unlink()
        return True
    return False

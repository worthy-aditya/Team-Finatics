"""sentinelai/health_command.py - Day 58 (Week 9).

The `health` Click command group.

Week 8 built the provider-health primitives (dashboard, history, alerts,
health-gated routing) and Day 57 added saveable/loadable health profiles - but
profiles could only be manipulated from Python, and the dashboard/alerts were
only reachable through `analyze` short-circuit flags. Day 58 gives provider
health a first-class CLI home:

    sentinelai health profiles                 # list saved profiles
    sentinelai health save NAME --scores '{...}'   # save a profile
    sentinelai health show NAME                # show a profile's scores
    sentinelai health delete NAME              # delete a profile
    sentinelai health status [--profile NAME]  # dashboard + alerts in one view

Built via a factory (like build_logs_command) so BOTH CLI entry points
(sentinelai/cli.py and the root sentinelai.py) register the identical command.

All subcommands are offline: no LLM or network calls.
"""

from __future__ import annotations

import json
from typing import Optional

import click

from sentinelai.ui import error, info, success, warn
from sentinelai.dashboard import build_dashboard
from sentinelai.health_alerts import build_alerts_report, detect_alerts
from sentinelai.health_history import (
    DEFAULT_HISTORY_PATH,
    load_history,
    record_snapshot,
    summarize_trends,
)
from sentinelai.health_profiles import (
    delete_profile,
    list_profiles,
    load_profile,
    save_profile,
)


def _parse_scores(scores_json: Optional[str], scores_file: Optional[str]) -> dict:
    """Resolve provider scores from a JSON string or a JSON file path."""
    if scores_file:
        with open(scores_file, encoding="utf-8") as fh:
            data = json.load(fh)
    elif scores_json:
        data = json.loads(scores_json)
    else:
        raise click.UsageError("provide scores via --scores JSON or --scores-file PATH")
    if not isinstance(data, dict) or not data:
        raise click.UsageError("scores must be a non-empty {provider: score} object")
    return data


def build_health_command():
    """Construct and return the shared `health` Click command group."""

    @click.group(name="health", help="Provider health: profiles, dashboard, and alerts (Weeks 8-9).")
    def health():
        """Inspect and manage LLM provider health state (offline)."""

    @health.command(name="profiles", help="List saved provider-health profiles.")
    def profiles():
        names = list_profiles()
        if not names:
            click.echo("No provider health profiles saved yet.")
            return
        click.echo("Saved provider health profiles:")
        for name in names:
            click.echo(f"  - {name}")

    @health.command(name="save", help="Save a provider-health profile.")
    @click.argument("name")
    @click.option("--scores", "scores_json", default=None,
                  help="Scores as a JSON object, e.g. '{\"gemini\": 90, \"ollama\": 80}'.")
    @click.option("--scores-file", "scores_file", default=None,
                  help="Path to a JSON file with the {provider: score} mapping.")
    def save(name, scores_json, scores_file):
        try:
            scores = _parse_scores(scores_json, scores_file)
            path = save_profile(name, scores)
        except (ValueError, json.JSONDecodeError, OSError) as exc:
            error(f"Could not save profile: {exc}")
            raise click.Abort()
        success(f"Saved provider health profile '{name}' -> {path}")

    @health.command(name="show", help="Show a saved provider-health profile.")
    @click.argument("name")
    def show(name):
        try:
            scores = load_profile(name)
        except (FileNotFoundError, ValueError) as exc:
            error(str(exc))
            raise click.Abort()
        click.echo(f"Provider health profile '{name}':")
        for provider, score in sorted(scores.items()):
            click.echo(f"  {provider:<12} {float(score):>6.1f}")

    @health.command(name="delete", help="Delete a saved provider-health profile.")
    @click.argument("name")
    def delete(name):
        try:
            removed = delete_profile(name)
        except ValueError as exc:
            error(str(exc))
            raise click.Abort()
        if removed:
            success(f"Deleted provider health profile '{name}'")
        else:
            warn(f"No provider health profile named '{name}'")

    @health.command(name="status", help="Show the health dashboard and any alerts in one view.")
    @click.option("--profile", "profile_name", default=None,
                  help="Use a saved profile's scores instead of the defaults.")
    @click.option("--record", is_flag=True,
                  help="Record the current scores to the history file first (Day 54).")
    def status(profile_name, record):
        scores = None
        if profile_name:
            try:
                scores = load_profile(profile_name)
            except (FileNotFoundError, ValueError) as exc:
                error(str(exc))
                raise click.Abort()
            info(f"Using provider health profile '{profile_name}'")

        # Dashboard (optionally recording a snapshot for history/trends).
        trends = None
        if record:
            snapshot_scores = scores or {"gemini": 80.0, "ollama": 78.0, "deepseek": 85.0}
            record_snapshot(snapshot_scores, path=DEFAULT_HISTORY_PATH)
            info(f"Recorded provider health snapshot to {DEFAULT_HISTORY_PATH}")
            trends = summarize_trends(load_history(DEFAULT_HISTORY_PATH))

        click.echo(build_dashboard(scores, trends=trends))

        # Alerts from recorded history (independent of the dashboard scores).
        click.echo()
        click.echo(build_alerts_report(detect_alerts(load_history(DEFAULT_HISTORY_PATH))))

    return health

"""
SentinelAI CLI - Main entry point
Note: This file is the entry point for the installed CLI.
The actual implementation is in sentinelai/cli.py
"""

import click

from sentinelai.ui import step  # noqa: F401  (reserved for command-level banners)
from commands.scan import scan
from commands.network import network
from commands.report import report
from commands.natural_cli import natural_cli
from commands.analyze import analyze
from commands.logs import logs
from sentinelai.health_command import build_health_command


@click.group(help="SentinelAI - AI Powered Cybersecurity CLI Agent")
@click.version_option(version="1.0.0", prog_name="SentinelAI")
def cli():
    """
    SentinelAI - AI Powered Cybersecurity CLI Agent

    Automates security investigations using natural language.
    Built by Team Finatics.
    """
    # Day 24 note: deliberately NO banner here. This callback runs before
    # every subcommand, so any stdout output would corrupt machine-readable
    # paths like `sentinelai logs --json` (piped JSON must stay clean).


cli.add_command(scan)
cli.add_command(network)
cli.add_command(report)
cli.add_command(natural_cli)
cli.add_command(analyze)
cli.add_command(logs)
# Day 58 parity: the `health` command group is registered on BOTH entry points
# via the shared factory (mirrors sentinelai/cli.py's main group).
cli.add_command(build_health_command())

if __name__ == "__main__":
    cli()

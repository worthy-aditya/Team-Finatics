"""
SentinelAI CLI - Main entry point
Note: This file is the entry point for the installed CLI.
The actual implementation is in sentinelai/cli.py
"""

import click
from rich.console import Console
from commands.scan import scan
from commands.network import network
from commands.report import report
from commands.natural_cli import natural_cli
from commands.analyze import analyze
from commands.logs import logs

console = Console()

@click.group(help="SentinelAI - AI Powered Cybersecurity CLI Agent")
@click.version_option(version="1.0.0", prog_name="SentinelAI")
def cli():
    """
    🛡️  SentinelAI - AI Powered Cybersecurity CLI Agent

    Automates security investigations using natural language.
    Built by Team Finatics.
    """
    pass

cli.add_command(scan)
cli.add_command(network)
cli.add_command(report)
cli.add_command(natural_cli)
cli.add_command(analyze)
cli.add_command(logs)

if __name__ == "__main__":
    cli()

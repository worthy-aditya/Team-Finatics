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

console = Console()

@click.group()
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

if __name__ == "__main__":
    cli()

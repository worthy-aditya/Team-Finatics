"""
Natural Language CLI command for commands folder
This is the entry point for the natural language interface
"""

import click
from sentinelai.natural_cli import NaturalLanguageCLI


@click.command()
@click.option("--llm", type=click.Choice(["claude", "gemini", "auto"]), default="auto",
              help="LLM to use for command interpretation")
def natural_cli(llm):
    """
    Command-based CLI for integrated SentinelAI features.

    Supported commands:
        scan
        network
        report
        help
        exit

    Examples:
        sentinelai natural-cli

        > scan localhost quickly
        > network
        > report
        > help
        > exit
    """
    cli = NaturalLanguageCLI()
    cli.run_interactive()

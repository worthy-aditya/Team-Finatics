import click
from rich.console import Console
from rich.panel import Panel

console = Console()

@click.group()
def cli():
    """SentinelAI - AI Powered Cybersecurity CLI Agent"""
    pass

@cli.command()
def start():
    """Start the SentinelAI agent"""
    console.print(Panel.fit(
        "[bold green]Welcome to SentinelAI CLI[/bold green]\n"
        "[cyan]Your AI-powered cybersecurity assistant[/cyan]",
        title="🛡️ SentinelAI",
        border_style="green"
    ))

if __name__ == "__main__":
    cli()
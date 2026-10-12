import click
from rich.console import Console
from rich.panel import Panel

# Import each teammate's command
from commands.scan import scan
from commands.network import network
from commands.report import report
from setup_wizard import run_setup_wizard

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

# Register each teammate's command
cli.add_command(scan)
cli.add_command(network)
cli.add_command(report)

@cli.command()
def start():
    """Start the SentinelAI interactive agent."""
    console.print(Panel.fit(
        "[bold green]Welcome to SentinelAI CLI[/bold green]\n"
        "[cyan]Your AI-powered cybersecurity assistant[/cyan]\n"
        "[white]Type --help to see all commands[/white]",
        title="🛡️ SentinelAI",
        border_style="green"
    ))


@cli.command()
@click.option("--provider", default="gemini", show_default=True, help="LLM provider to configure: gemini, ollama, or mistral.")
@click.option("--model", default=None, help="Optional model name for the selected provider.")
@click.option("--privacy/--no-privacy", default=False, help="Enable privacy mode for offline-only operation.")
def setup(provider, model, privacy):
    """Create a local .env configuration for a fresh machine."""
    config = run_setup_wizard(provider=provider, model=model, privacy_mode=privacy)
    console.print("[green]Fresh-machine setup complete.[/green]")
    for key, value in config.items():
        console.print(f"[cyan]{key}=[/cyan]{value}")


if __name__ == "__main__":
    cli()
import click
from rich.console import Console

console = Console()

@click.command()
@click.argument("target", required=False)
def scan(target):
    """Run security scan on a target IP or domain."""
    if target:
        console.print(f"[cyan]Scanning target: {target}[/cyan]")
    else:
        console.print("[yellow]Provide a target. Example: python sentinelai.py scan 192.168.1.1[/yellow]")
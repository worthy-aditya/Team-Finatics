import click
from rich.console import Console

console = Console()

@click.command()
@click.argument("domain", required=False)
def network(domain):
    """Run network tools like DNS lookup and subdomain finder."""
    if domain:
        console.print(f"[cyan]Running network tools on: {domain}[/cyan]")
    else:
        console.print("[yellow]Provide a domain. Example: python sentinelai.py network google.com[/yellow]")
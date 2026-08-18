import click
import socket
import platform
from colorama import Fore, Style, init

init(autoreset=True)

@click.command()
def network():
    """Display network information and interface details."""
    click.echo(f"{Fore.CYAN}[*] Gathering network information...{Style.RESET_ALL}\n")
    
    # Get hostname
    try:
        hostname = socket.gethostname()
        click.echo(f"{Fore.GREEN}Hostname:{Style.RESET_ALL} {hostname}")
    except:
        click.echo(f"{Fore.RED}[!] Could not retrieve hostname{Style.RESET_ALL}")
    
    # Get local IP
    try:
        local_ip = socket.gethostbyname(hostname)
        click.echo(f"{Fore.GREEN}Local IP:{Style.RESET_ALL} {local_ip}")
    except:
        click.echo(f"{Fore.RED}[!] Could not retrieve local IP{Style.RESET_ALL}")
    
    # Get OS info
    try:
        os_info = platform.system()
        os_version = platform.release()
        click.echo(f"{Fore.GREEN}Operating System:{Style.RESET_ALL} {os_info} {os_version}")
    except:
        click.echo(f"{Fore.RED}[!] Could not retrieve OS info{Style.RESET_ALL}")
    
    # Get Python version
    try:
        python_version = platform.python_version()
        click.echo(f"{Fore.GREEN}Python Version:{Style.RESET_ALL} {python_version}")
    except:
        click.echo(f"{Fore.RED}[!] Could not retrieve Python version{Style.RESET_ALL}")
    
    click.echo("\n" + "=" * 60)
    click.echo(f"{Fore.YELLOW}💡 Tip: Use 'sentinelai scan --target <IP>' to scan this system or others{Style.RESET_ALL}")

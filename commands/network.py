import click
import socket
import platform

from sentinelai.ui import error, info, kv, warn

@click.command()
def network():
    """Display network information and interface details."""
    info("Gathering network information...")
    click.echo()
    
    # Get hostname
    try:
        hostname = socket.gethostname()
        kv("Hostname", hostname)
    except Exception:
        error("Could not retrieve hostname")
    
    # Get local IP
    try:
        local_ip = socket.gethostbyname(hostname)
        kv("Local IP", local_ip)
    except Exception:
        error("Could not retrieve local IP")
    
    # Get OS info
    try:
        os_info = platform.system()
        os_version = platform.release()
        kv("Operating System", f"{os_info} {os_version}")
    except Exception:
        error("Could not retrieve OS info")
    
    # Get Python version
    try:
        python_version = platform.python_version()
        kv("Python Version", python_version)
    except Exception:
        error("Could not retrieve Python version")
    
    click.echo()
    warn("Tip: Use 'sentinelai scan --target <IP>' to scan this system or others")

"""
Natural Language CLI Interface for SentinelAI
Allows users to interact with security tools using plain English
Powered by Claude/Gemini AI for command interpretation
"""

import os
import re
import json
import sys
import random
import logging
from typing import Dict, Tuple, Optional
from dotenv import load_dotenv
import click
from colorama import Fore, Style, init

# Disable verbose logging from external libraries
logging.getLogger('google').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Load environment variables
load_dotenv()

# Import scanner and report modules
from sentinelai.scanner import NmapScanner, Scanner
from sentinelai.prompt_engine import analyze_scan_file


class NaturalLanguageCLI:
    """
    AI-powered CLI that interprets natural language commands
    Maps user intent to appropriate security scanning operations
    """

    def __init__(self):
        """Initialize the natural language CLI"""
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.claude_key = os.getenv("CLAUDE_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.conversation_history = []
        self.session_scans = {}

        # Try to import Claude (Anthropic)
        self.claude_available = False
        if self.claude_key:
            try:
                import anthropic
                self.claude_client = anthropic.Anthropic(api_key=self.claude_key)
                self.claude_available = True
            except ImportError:
                pass

        # Try to import Gemini
        self.gemini_available = False
        self.genai_client = None
        if self.gemini_key:
            try:
                from google import genai
                self.genai = genai
                self.genai_client = genai.Client(api_key=self.gemini_key)
                self.gemini_available = True
            except Exception as e:
                self.gemini_available = False

    def parse_intent(self, user_input: str) -> Dict:
        """
        Parse user's natural language input to extract intent and parameters
        Uses AI to understand what the user wants to do
        
        Returns:
            Dict with keys: 'action', 'target', 'scan_type', 'format', 'confidence'
        """
        
        # System prompt for the AI
        system_prompt = """You are a cybersecurity CLI interpreter. 
        
Analyze the user's input and determine:
1. ACTION: What they want to do (scan, analyze, report, network, help, exit)
2. TARGET: What target to scan (IP, domain, or localhost)
3. SCAN_TYPE: How aggressive (fast=20 ports, standard=1000 ports, aggressive=full)
4. FORMAT: Report format (text, json, csv)

Respond ONLY in valid JSON format like this:
{
  "action": "scan",
  "target": "127.0.0.1",
  "scan_type": "fast",
  "format": "text",
  "confidence": 0.95,
  "explanation": "User wants to quickly scan localhost"
}

Valid actions: scan, analyze, report, network, help, exit
Scan types: fast (20 ports), standard (1000 ports), aggressive (full)
Formats: text, json, csv

If the input is not a supported command, return:
{"action": "unknown", "confidence": 0.0, "message": "Unsupported command. Supported commands: scan, analyze, network, report, help, exit"}"""

        try:
            # Use Claude if available, fallback to Gemini
            if self.claude_available:
                message = self.claude_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=200,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_input}]
                )
                response_text = message.content[0].text
            elif self.gemini_available and self.genai_client:
                message = self.genai_client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=f"{system_prompt}\n\nUser input: {user_input}"
                )
                response_text = message.text
            else:
                # Fallback: Simple regex parsing if no AI available
                return self._simple_parse(user_input)

            # Parse JSON response
            try:
                intent = json.loads(response_text)
                return intent
            except json.JSONDecodeError:
                # If JSON parsing fails, try simple parsing
                return self._simple_parse(user_input)

        except Exception as e:
            click.echo(f"{Fore.YELLOW}[!] AI parsing error: {str(e)}{Style.RESET_ALL}")
            return self._simple_parse(user_input)

    def _simple_parse(self, user_input: str) -> Dict:
        """
        Fallback parser using regex patterns when AI is unavailable
        Still provides reasonable command interpretation
        """
        user_input_lower = user_input.lower()
        
        # Only support commands that are already integrated in the project.
        command_verbs = ["scan", "analyze", "analysis", "report", "network", "help", "exit", "quit", "generate", "show", "display", "info"]

        has_command_verb = any(keyword in user_input_lower for keyword in command_verbs)

        # Unknown / unsupported input should never trigger an action by itself.
        if not has_command_verb:
            return {
                "action": "unknown",
                "message": "Unsupported command. Use one of: scan, analyze, network, report, help, exit",
                "confidence": 0.0
            }

        # Determine action
        if "exit" in user_input_lower or "quit" in user_input_lower:
            return {"action": "exit", "confidence": 0.9}
        elif "network" in user_input_lower or "info" in user_input_lower:
            return {"action": "network", "confidence": 0.8}
        elif "analyze" in user_input_lower or "analysis" in user_input_lower:
            return {"action": "analyze", "confidence": 0.8}
        elif "report" in user_input_lower or "generate" in user_input_lower:
            return {"action": "report", "format": "text", "confidence": 0.7}
        elif "help" in user_input_lower or "?" in user_input_lower:
            return {"action": "help", "confidence": 0.9}

        # Default to scan only if a command verb is explicitly present.
        action = "scan"

        # Extract target
        target = None
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        domain_pattern = r'(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}'
        
        ip_match = re.search(ip_pattern, user_input)
        if ip_match:
            target = ip_match.group()
        else:
            domain_match = re.search(domain_pattern, user_input.lower())
            if domain_match:
                target = domain_match.group()
            elif "localhost" in user_input_lower or "127.0.0.1" in user_input_lower or "local" in user_input_lower:
                target = "127.0.0.1"
        
        # Determine scan type
        scan_type = "standard"
        if "fast" in user_input_lower or "quick" in user_input_lower or "top" in user_input_lower:
            scan_type = "fast"
        elif "aggressive" in user_input_lower or "full" in user_input_lower or "deep" in user_input_lower:
            scan_type = "aggressive"
        
        # Determine format
        format_type = "text"
        if "json" in user_input_lower:
            format_type = "json"
        elif "csv" in user_input_lower:
            format_type = "csv"
        
        return {
            "action": action,
            "target": target or "127.0.0.1",
            "scan_type": scan_type,
            "format": format_type,
            "confidence": 0.7
        }

    def execute_command(self, intent: Dict) -> Tuple[bool, str]:
        """
        Execute the interpreted command based on intent
        Returns: (success, output_message)
        """
        action = intent.get("action", "scan")
        
        try:
            if action == "exit" or action == "quit":
                return True, "exit"

            elif action == "unknown":
                return False, intent.get("message", "Unsupported command. Use one of: scan, network, report, help, exit")

            elif action == "help":
                return True, self._get_help_text()
            
            elif action == "network":
                return self._execute_network_command()
            
            elif action == "report":
                return self._execute_report_command(intent)
            
            elif action == "scan":
                return self._execute_scan_command(intent)
            
            elif action == "analyze":
                return self._execute_analyze_command(intent)
            
            else:
                return False, f"Unknown action: {action}"
        
        except Exception as e:
            return False, f"Error executing command: {str(e)}"

    def _execute_scan_command(self, intent: Dict) -> Tuple[bool, str]:
        """Execute network scan"""
        target = intent.get("target", "127.0.0.1")
        scan_type = intent.get("scan_type", "standard")
        
        # Validate target
        if not Scanner.validate_target(target):
            return False, f"❌ Invalid target: {target}"
        
        # Build Nmap arguments based on scan type
        if scan_type == "fast":
            arguments = "-p 22,80,443,3306,5432,8080,8443,25,53,110,143,3389,1433,27017,5000,5900,9200,9300,11211,6379"
            time_estimate = "~30 seconds"
        elif scan_type == "aggressive":
            arguments = "-sV -sC -A -p- --script vuln"
            time_estimate = "~5-10 minutes"
        else:  # standard
            arguments = "-sV -p 1-1000"
            time_estimate = "~2-3 minutes"
        
        click.echo(f"\n{Fore.CYAN}🔍 Scanning {target} ({scan_type} mode - {time_estimate})...{Style.RESET_ALL}")
        
        # Execute scan
        scanner = NmapScanner(target)
        scanner.scan(arguments=arguments)
        
        if scanner.scan_errors:
            return False, f"Scan completed with errors:\n" + "\n".join(scanner.scan_errors)
        
        # Get results
        summary = scanner.get_summary()
        open_ports = scanner.get_open_ports()
        
        # Store in session
        self.session_scans[target] = scanner
        
        # Format output
        output = f"\n{Fore.GREEN}✅ Scan completed!{Style.RESET_ALL}\n"
        output += summary
        
        if open_ports:
            output += f"\n{Fore.YELLOW}Found {len(open_ports)} open ports:{Style.RESET_ALL}\n"
            for port in open_ports[:5]:  # Show first 5
                output += f"  • Port {port['port']}/{port['protocol']}: {port['service']}\n"
        
        return True, output

    def _execute_report_command(self, intent: Dict) -> Tuple[bool, str]:
        """Generate security report"""
        format_type = intent.get("format", "text")
        
        if not os.path.exists("scan_results.json"):
            return False, "❌ No scan results found. Please run a scan first."
        
        try:
            click.echo(f"\n{Fore.CYAN}📄 Generating {format_type} report...{Style.RESET_ALL}")
            
            with open("scan_results.json") as f:
                data = json.load(f)
            
            if format_type == "json":
                output = json.dumps(data, indent=2)
            else:
                # Simple text report from JSON
                output = self._format_text_report(data)
            
            return True, f"{Fore.GREEN}✅ Report generated!{Style.RESET_ALL}\n\n{output}"
        
        except Exception as e:
            return False, f"❌ Report generation failed: {str(e)}"
    
    def _format_text_report(self, data: Dict) -> str:
        """Format scan data as text report"""
        report = "=" * 60 + "\n"
        report += "SENTINELAI SECURITY REPORT\n"
        report += "=" * 60 + "\n\n"
        
        if "scan_summary" in data:
            report += f"Scan Time: {data.get('scan_time', 'Unknown')}\n"
            report += f"Target: {data.get('target', 'Unknown')}\n"
            report += f"Hosts Up: {data.get('hosts_up', 0)}\n"
            report += f"Hosts Down: {data.get('hosts_down', 0)}\n"
        
        if "hosts" in data:
            for host in data["hosts"]:
                report += f"\n{Fore.YELLOW}Host: {host.get('hostname', 'Unknown')}{Style.RESET_ALL}\n"
                if "ports" in host:
                    for port in host["ports"]:
                        if port.get("state") == "open":
                            report += f"  Port {port['port']}/{port['protocol']}: {port.get('service', 'Unknown')}\n"
        
        report += "\n" + "=" * 60 + "\n"
        return report

    def _execute_network_command(self) -> Tuple[bool, str]:
        """Display network information"""
        try:
            import socket
            import platform
            
            click.echo(f"\n{Fore.CYAN}📡 Gathering network information...{Style.RESET_ALL}")
            
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            os_info = platform.system()
            os_version = platform.release()
            python_version = platform.python_version()
            
            output = f"""
{Fore.GREEN}✅ Network Information:{Style.RESET_ALL}
  Hostname: {hostname}
  Local IP: {local_ip}
  OS: {os_info} {os_version}
  Python: {python_version}
"""
            return True, output
        
        except Exception as e:
            return False, f"❌ Failed to get network info: {str(e)}"

    def _execute_analyze_command(self, intent: Dict) -> Tuple[bool, str]:
        """Analyze scan results using Gemini"""
        input_file = intent.get("input_file", "scan_results.json")

        try:
            model, analysis = analyze_scan_file(input_file=input_file)
        except Exception as e:
            return False, f"Analysis failed: {str(e)}"

        output = f"""
{Fore.CYAN}AI Analysis generated with {model}:{Style.RESET_ALL}

{analysis}
"""
        return True, output

        target = intent.get("target")
        
        if target and target in self.session_scans:
            scanner = self.session_scans[target]
            summary = scanner.get_summary()
            
            output = f"""
{Fore.CYAN}🤖 AI Analysis of {target}:{Style.RESET_ALL}

{Fore.YELLOW}This feature requires LLM integration.{Style.RESET_ALL}
{Fore.YELLOW}Coming in Week 2 with prompt_engine.py!{Style.RESET_ALL}

{Fore.GREEN}Scan Summary:{Style.RESET_ALL}
{summary}
"""
            return True, output
        
        return False, "No scan data to analyze. Please run a scan first."

    def _get_help_text(self) -> str:
        """Return help text for integrated commands only"""
        return f"""
{Fore.GREEN}╔════════════════════════════════════════════════════════╗
║              🛡️  SentinelAI Command CLI                   ║
╚════════════════════════════════════════════════════════════╝{Style.RESET_ALL}

{Fore.CYAN}Supported commands:{Style.RESET_ALL}
  • scan
  • network
  • report
  • help
  • exit

{Fore.YELLOW}Examples:{Style.RESET_ALL}
  • "scan localhost quickly"
  • "scan 127.0.0.1 fast"
  • "network"
  • "report"
  • "generate json report"
  • "help"
  • "exit"

{Fore.YELLOW}Scan Types:{Style.RESET_ALL}
  • fast: Quick scan (top 20 ports, ~30 seconds)
  • standard: Normal scan (1000 ports, ~2-3 minutes)
  • aggressive: Full scan (all ports + scripts, ~5-10 minutes)

{Fore.GREEN}Only the integrated SentinelAI commands are supported.{Style.RESET_ALL}
"""

    def run_interactive(self):
        """Run the interactive CLI loop"""
        click.clear()
        click.echo(f"""
{Fore.GREEN}╔════════════════════════════════════════════════════════╗
║           🛡️  SentinelAI - Command CLI                     ║
║             Scan / Network / Report commands               ║
╚════════════════════════════════════════════════════════════╝{Style.RESET_ALL}

Type a supported command.
Examples: 'scan localhost quickly', 'network', 'report', 'help', 'exit'
""")

        while True:
            try:
                # Get user input with clear prompt
                user_input = click.prompt(f"{Fore.CYAN}You{Style.RESET_ALL}", type=str).strip()
                
                if not user_input:
                    continue
                
                # Parse intent using AI
                intent = self.parse_intent(user_input)
                
                # Check confidence and action
                action = intent.get("action")
                confidence = intent.get("confidence", 0.5)

                # Only show confidence for ambiguous commands
                if confidence < 0.7 and action != "unknown":
                    click.echo(f"{Fore.YELLOW}[?] Understood: {action.upper()} (confidence: {confidence:.0%}){Style.RESET_ALL}")

                # Execute command
                success, output = self.execute_command(intent)

                if output == "exit":
                    click.echo(f"\n{Fore.GREEN}👋 Goodbye!{Style.RESET_ALL}")
                    break

                if success:
                    click.echo(f"\n{Fore.GREEN}AI{Style.RESET_ALL}:\n{output}\n")
                else:
                    click.echo(f"\n{Fore.RED}❌ {output}{Style.RESET_ALL}\n")
                
                # Add to conversation history
                self.conversation_history.append({
                    "user": user_input,
                    "intent": intent,
                    "success": success
                })

            except KeyboardInterrupt:
                click.echo(f"\n{Fore.YELLOW}[*] Interrupted by user{Style.RESET_ALL}")
                break
            except Exception as e:
                click.echo(f"{Fore.RED}❌ Error: {str(e)}{Style.RESET_ALL}\n")


@click.command()
@click.option("--llm", type=click.Choice(["claude", "gemini", "auto"]), default="auto",
              help="LLM to use for command interpretation")
def natural_cli(llm):
    """
    Natural Language CLI Interface for SentinelAI
    
    Start an interactive session where you can use plain English commands
    to run security scans and generate reports.
    
    Example:
        sentinelai natural-cli
        > scan localhost quickly
        > show network info
        > generate a report
    """
    cli = NaturalLanguageCLI()
    
    # Check AI availability
    if llm == "claude" and not cli.claude_available:
        click.echo(f"{Fore.YELLOW}[!] Claude API not configured. Using Gemini or fallback.{Style.RESET_ALL}")
    elif llm == "gemini" and not cli.gemini_available:
        click.echo(f"{Fore.YELLOW}[!] Gemini API not configured. Using Claude or fallback.{Style.RESET_ALL}")
    
    if not cli.claude_available and not cli.gemini_available:
        click.echo(f"{Fore.YELLOW}[!] No AI available. Using rule-based command parsing.{Style.RESET_ALL}")
    
    # Start interactive session
    cli.run_interactive()


if __name__ == "__main__":
    natural_cli()

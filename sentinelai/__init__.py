"""
SentinelAI CLI - AI-powered defensive security agent
Orchestrates security tools through natural-language interface
"""

__version__ = "0.1.0"
__author__ = "Team Finatics"

from .cli import main
from .scanner import Scanner

__all__ = ["main", "Scanner"]

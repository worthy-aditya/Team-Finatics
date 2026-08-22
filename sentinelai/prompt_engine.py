"""
Prompt engine for SentinelAI scan analysis.

This module owns the reusable Day 9 flow:
structured Nmap JSON -> LLM prompt -> plain-English analysis.
"""

import json
import os
import socket
from pathlib import Path
from typing import Iterable, Optional, Tuple, Union

from dotenv import load_dotenv
from google import genai


DEFAULT_SCAN_INPUT_FILE = Path("scan_results.json")
DEFAULT_ANALYSIS_OUTPUT_FILE = Path("day9_nmap_llm_analysis.md")

DEFAULT_GEMINI_MODELS = [
    "gemini-3.6-flash",
    "gemini-flash-latest",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
]

GEMINI_API_HOST = "generativelanguage.googleapis.com"

NMAP_ANALYSIS_PROMPT = """
You are a cybersecurity analyst assistant helping a student understand
the security implications of a network scan.

Below is structured Nmap scan output (JSON) for a target host:

{scan_data}

Please provide:
1. A plain-English summary of what was found: hosts, open ports, services, and versions.
2. The highest-risk findings, ranked by likely security impact.
3. What an attacker could potentially infer or attempt from this information.
4. Practical next steps for a defender to verify or reduce the risk.

Keep the explanation clear enough for someone learning cybersecurity,
but technically accurate. Do not claim a vulnerability exists unless the scan data
actually supports that conclusion.
"""


PathLike = Union[str, Path]


def load_scan_data(path: PathLike = DEFAULT_SCAN_INPUT_FILE) -> dict:
    """Load structured scan data from a JSON file."""
    scan_path = Path(path)
    if not scan_path.exists():
        raise FileNotFoundError(f"Missing scan input file: {scan_path}")

    with scan_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_nmap_analysis_prompt(scan_data: dict) -> str:
    """Build the Nmap analysis prompt from structured scan JSON."""
    return NMAP_ANALYSIS_PROMPT.format(scan_data=json.dumps(scan_data, indent=2))


def _model_candidates(preferred_model: Optional[str] = None) -> Iterable[str]:
    """Return configured Gemini models in the order they should be tried."""
    seen = set()
    for model in [preferred_model, os.getenv("GEMINI_MODEL"), *DEFAULT_GEMINI_MODELS]:
        if model and model not in seen:
            seen.add(model)
            yield model


def check_gemini_network() -> None:
    """Fail early with a clear message when Gemini's API host cannot be resolved."""
    try:
        socket.getaddrinfo(GEMINI_API_HOST, 443)
    except socket.gaierror as exc:
        raise RuntimeError(
            "Cannot resolve Gemini API host "
            f"({GEMINI_API_HOST}). This is a DNS/internet connectivity issue, "
            "not a prompt or model issue. Check your internet connection, DNS settings, "
            "VPN/proxy, firewall, or whether Google Gemini API access is blocked on this network."
        ) from exc


def generate_nmap_analysis(
    scan_data: dict,
    preferred_model: Optional[str] = None,
) -> Tuple[str, str]:
    """Generate plain-English Nmap analysis with Gemini fallback models."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set. Add it to .env before running analysis.")

    check_gemini_network()

    client = genai.Client(api_key=api_key)
    prompt = build_nmap_analysis_prompt(scan_data)
    errors = []

    for model in _model_candidates(preferred_model):
        try:
            response = client.models.generate_content(model=model, contents=prompt)
            return model, response.text
        except Exception as exc:
            errors.append(f"{model}: {exc}")

    raise RuntimeError("All Gemini model attempts failed:\n" + "\n".join(errors))


def analyze_scan_file(
    input_file: PathLike = DEFAULT_SCAN_INPUT_FILE,
    output_file: Optional[PathLike] = DEFAULT_ANALYSIS_OUTPUT_FILE,
    preferred_model: Optional[str] = None,
) -> Tuple[str, str]:
    """Analyze a scan JSON file and optionally save the Markdown output."""
    scan_data = load_scan_data(input_file)
    model, analysis = generate_nmap_analysis(scan_data, preferred_model=preferred_model)

    if output_file:
        output_path = Path(output_file)
        output = f"# Day 9 Nmap LLM Analysis\n\nModel: `{model}`\n\n{analysis}\n"
        output_path.write_text(output, encoding="utf-8")

    return model, analysis

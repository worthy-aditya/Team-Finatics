"""
Prompt engine for SentinelAI scan analysis.

This module owns the reusable Nmap -> LLM -> analysis flow (Days 9-10):
structured Nmap JSON -> refined risk-focused prompt -> plain-English
security analysis with risk scoring and actionable next steps.
"""

import json
import os
import socket
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable, List, Optional, Tuple, Union

from dotenv import load_dotenv
from google import genai
from google.genai import types


DEFAULT_SCAN_INPUT_FILE = Path("scan_results.json")
DEFAULT_ANALYSIS_OUTPUT_FILE = Path("day9_nmap_llm_analysis.md")

DEFAULT_GEMINI_MODELS = [
    "gemini-3.6-flash",
    "gemini-flash-latest",
    "gemini-3.5-flash",
    "gemini-3.7-flash",
]

# Long per-request timeout: Gemini can take 2-5 minutes to generate a
# full security analysis for a realistic scan.
GEMINI_REQUEST_TIMEOUT_MS = 300_000

# Transient API errors worth retrying with backoff.
RETRYABLE_STATUS = {429, 500, 503}

GEMINI_API_HOST = "generativelanguage.googleapis.com"


class LLMProvider(str, Enum):
    """Supported LLM providers (extended progressively in later days)."""

    GEMINI = "gemini"
    OPENAI = "openai"
    CLAUDE = "claude"
    OLLAMA = "ollama"


class PromptMode(str, Enum):
    """Prompt modes selectable by the engine."""

    STANDARD = "standard"
    BEGINNER = "beginner"
    REMEDIATION = "remediation"


@dataclass
class ScanAnalysisResult:
    """Structured result of a scan analysis (provider-agnostic).

    Holds whatever data the analysis produced so callers don't need to
    know which LLM provider actually answered the prompt.
    """

    provider: LLMProvider
    model: str
    analysis: str
    prompt: str = ""
    raw: Optional[dict] = None
    usage: dict = field(default_factory=dict)


DEFAULT_MODEL_BY_PROVIDER: dict = {
    LLMProvider.GEMINI: "gemini-2.0-flash",
}

# Optional override via environment, e.g. GEMINI_MODEL=gemini-1.5-flash
_ENV_MODEL_BY_PROVIDER: dict = {
    LLMProvider.GEMINI: os.getenv("GEMINI_MODEL"),
    LLMProvider.OPENAI: os.getenv("OPENAI_MODEL"),
    LLMProvider.CLAUDE: os.getenv("CLAUDE_MODEL"),
    LLMProvider.OLLAMA: os.getenv("OLLAMA_MODEL"),
}


def default_models_for_provider(provider: LLMProvider) -> List[str]:
    """Return the list of fallback models for a provider, provider-specific first."""
    env_model = _ENV_MODEL_BY_PROVIDER.get(provider)
    base = DEFAULT_MODEL_BY_PROVIDER.get(provider, "")
    ordered: List[str] = []
    for m in (env_model, base):
        if m and m not in ordered:
            ordered.append(m)
    if provider is LLMProvider.GEMINI:
        for m in DEFAULT_GEMINI_MODELS:
            if m not in ordered:
                ordered.append(m)
    return ordered

NMAP_ANALYSIS_PROMPT = """
You are a senior cybersecurity analyst assistant helping a student understand
the security implications of a network scan. Your analysis must be
strictly evidence-based: base every conclusion only on the scan data provided,
and never claim a vulnerability exists unless the scan output supports it.

IMPORTANT CONTEXT: You are assisting with DEFENSIVE security education and
hardening. The scan data below was collected as part of a learning exercise or
authorized assessment of the user's own system or network (or a public test
target such as scanme.nmap.org, which is run by Nmap for practicing scans).
Focus on understanding, risk awareness, and remediation. Do NOT provide
step-by-step exploitation instructions, attack playbooks, or specific exploit
commands. Frame everything from a defender's perspective.

Below is structured Nmap scan output (JSON) for a target host:

{scan_data}

Produce a Markdown analysis with EXACTLY these sections, in this order:

## 1. Plain-English Summary
A short, beginner-friendly overview: the target, host status, total open ports,
notable services and versions, and what kind of system this appears to be.

## 2. Risk Findings (ranked)
For EACH open or unusual port, provide a structured finding:
- **Risk #N - <service name> (port <port>/<protocol>)**
  - Severity: <Critical|High|Medium|Low> (score out of 10)
  - Evidence from scan: state, product, version, extra info exactly as reported
  - Why it matters: plain-English explanation of the associated risk
Rank every finding from highest to lowest severity. If a service is only
"filtered" or closed, explain it briefly but do not rank it with open ports.

## 3. Attacker Perspective
- For DEFENSIVE awareness only: briefly what an attacker would infer about the
  host (OS, role, service versions) from the banner data, WITHOUT providing a
  step-by-step attack playbook.
- Mention at a high level the categories of techniques an attacker could use
  against each open service (e.g., credential attacks, web scanning), so a
  defender knows what to guard against.
- Concretely list Nmap NSE scripts a DEFENDER can run to audit own services.
- Clearly state what the scan DOES prove and what it DOES NOT prove

## 4. Recommended Next Steps
Split into two numbered groups, each tied to the specific service(s) it addresses:
### Immediate (verification)
Steps, tools, or commands a defender can run right now to confirm or eliminate
each risk (e.g., targeted Nmap scripts, configuration checks, log review).
### Hardening (medium-term)
Steps to reduce or remove the exposure over the next days (patching, firewall
rules, disabling unused services, access restrictions).

## 5. Confidence & Limitations
- Which findings are strongly supported by the scan versus speculative
- What additional scans or data sources would improve confidence
  (e.g., full -sV port sweep, Nmap vulnerability scripts, Windows Event Logs)

Keep the tone educational for a security learner but technically accurate.
Do not fabricate scan results that are not present in the JSON above.
"""


# ---------------------------------------------------------------------------
# Day 11: Additional prompt templates (reusable, composable)
# ---------------------------------------------------------------------------

# Beginner variant — simpler language, extra definitions, "what to learn next"
NMAP_ANALYSIS_BEGINNER_PROMPT = """
You are a friendly cybersecurity teacher helping a BEGINNER student understand
their first network scan. Use very simple language, define any jargon on first
use, and add a short "Learning Takeaway" line for each finding.

IMPORTANT CONTEXT: This is a DEFENSIVE, education-focused analysis of the user's
own scan data. Do NOT provide exploitation instructions or exploit commands.

Below is structured Nmap scan output (JSON) for a target host:

{scan_data}

Produce a Markdown analysis with these sections (simpler wording throughout):
## 1. What is this scan about?
A non-technical explanation: what was scanned, why it ran, and that open = "a
service is listening", filtered = "a firewall blocked the check".
## 2. What did we see?
For each open port: the port number, the service name in plain words, and one
short sentence of what that service does (e.g. "SSH / port 22 — used to log in
to a computer remotely").
## 3. Easy risk ratings
For each open/unusual port, give:
- **Finding #N - <service name> (port <port>/<protocol>)**
  - How risky: Low / Medium / High — and in one simple sentence why
  - Learning Takeaway: one sentence a beginner should remember
## 4. What should we do next?
A short, plain-English checklist (4-6 bullet points) anyone can follow.
## 5. Glossary
Define any technical terms you used (port, service, version, protocol, etc.).

Tone: warm, encouraging, jargon-free. Do not fabricate scan results.
"""

# Remediation variant — focused on fix/verification steps
NMAP_REMEDIATION_PROMPT = """
You are a practical cybersecurity engineer. Given the scan findings below,
produce an action-oriented remediation plan focused on verification and
hardening. Keep it strictly defensive (no exploit instructions).

IMPORTANT CONTEXT: The data was collected for a learning exercise or an
authorized assessment of the user's own system/network (or a public test target
like scanme.nmap.org). Focus on hardening and verification.

Below is structured Nmap scan output (JSON) for a target host:

{scan_data}

Produce a Markdown remediation plan with these sections, in order:
## 1. Executive Summary
One short paragraph: what this system is, how many findings need attention,
and the single most important immediate action.
## 2. Prioritized Action List
For EACH open or unusual port, produce a remediation card:
- **Finding #N - <service name> (port <port>/<protocol>)**
  - Risk rating: <High|Medium|Low>
  - Verify now: 1-2 concrete diagnostic steps or commands a defender can run
  - Fix: concrete hardening steps (patch, disable, firewall, config change)
  - Reference: a short mention of the framework or guidance source (e.g.,
    "CIS Windows Benchmark", "OWASP ASVS") — do not invent URLs
## 3. Compliance Cross-Check
Map each finding to the most relevant OWASP Top 10 category and MITRE ATT&CK
tactic. If a finding does not clearly map, say so rather than forcing a match.
## 4. Verification Plan
A short checklist a defender can use AFTER remediation to confirm the fix
worked (re-run which ports, what "closed" / "filtered" looks like, which NSE
scripts to re-run).

Do not fabricate findings not present in the scan data. Keep it concise and
actionable.
"""


def _select_prompt_template(mode: PromptMode) -> str:
    """Return the prompt template string for a given prompt mode."""
    if mode is PromptMode.BEGINNER:
        return NMAP_ANALYSIS_BEGINNER_PROMPT
    if mode is PromptMode.REMEDIATION:
        return NMAP_REMEDIATION_PROMPT
    return NMAP_ANALYSIS_PROMPT


def build_prompt(scan_data: dict, mode: PromptMode = PromptMode.STANDARD) -> str:
    """Build a scan-analysis prompt for the requested mode.

    Args:
        scan_data: structured scan dict.
        mode: STANDARD (risk + next steps), BEGINNER (simple language),
              or REMEDIATION (verification + hardening plan).
    """
    template = _select_prompt_template(mode)
    return template.format(scan_data=json.dumps(scan_data, indent=2))


def build_nmap_analysis_prompt(
    scan_data: dict, mode: PromptMode = PromptMode.STANDARD
) -> str:
    """Backwards-compatible alias for build_prompt() (Day 9-10 callers)."""
    return build_prompt(scan_data, mode=mode)


PathLike = Union[str, Path]


def load_scan_data(path: PathLike = DEFAULT_SCAN_INPUT_FILE) -> dict:
    """Load structured scan data from a JSON file."""
    scan_path = Path(path)
    if not scan_path.exists():
        raise FileNotFoundError(f"Missing scan input file: {scan_path}")

    with scan_path.open("r", encoding="utf-8") as f:
        return json.load(f)


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


def force_ipv4_resolution() -> None:
    """
    Force IPv4 (AF_INET) DNS resolution for hosts without working IPv6.

    The google-genai httpx client can hang for minutes when a hostname resolves
    to both A (IPv4) and AAAA (IPv6) records but the machine has no IPv6 route
    (common on Windows corporate/college networks). This monkeypatch filters
    getaddrinfo() results to IPv4 so every provider connection succeeds fast.
    """
    import fnmatch

    original_getaddrinfo = socket.getaddrinfo

    def _ipv4_only_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        if isinstance(host, str) and (
            "googleapis.com" in host
            or "generativelanguage" in host
            or fnmatch.fnmatch(host, "*.ai")
        ):
            family = socket.AF_INET
        return original_getaddrinfo(host, port, family, type, proto, flags)

    socket.getaddrinfo = _ipv4_only_getaddrinfo


def generate_nmap_analysis(
    scan_data: dict,
    preferred_model: Optional[str] = None,
    retries: int = 2,
) -> Tuple[str, str]:
    """Generate plain-English Nmap analysis with Gemini fallback models."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set. Add it to .env before running analysis.")

    check_gemini_network()
    force_ipv4_resolution()

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=GEMINI_REQUEST_TIMEOUT_MS),
    )
    prompt = build_nmap_analysis_prompt(scan_data)
    errors = []

    # Explicit safety settings: this is a DEFENSIVE, education-focused analysis of
    # the user's own scan data. Lower the automatic safety-blocking threshold for
    # benign security topics so the model does not refuse to help with the
    # analysis (it can still block genuinely harmful requests).
    safety_settings = [
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        ),
    ]

    for model in _model_candidates(preferred_model):
        for attempt in range(retries + 1):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        safety_settings=safety_settings,
                    ),
                )
                return model, response.text
            except Exception as exc:
                status = getattr(exc, "code", None) or getattr(exc, "status_code", None)
                reason = f"{model} (attempt {attempt + 1}): {exc}"
                errors.append(reason)
                is_retryable = status in RETRYABLE_STATUS or isinstance(
                    exc, TimeoutError
                )
                if attempt < retries and is_retryable:
                    backoff = 5 * (2 ** attempt)
                    print(f"[*] Retrying {model} in {backoff}s after: {exc}")
                    time.sleep(backoff)

    raise RuntimeError("All Gemini model attempts failed:\n" + "\n".join(errors))


def analyze_scan_file(
    input_file: PathLike = DEFAULT_SCAN_INPUT_FILE,
    output_file: Optional[PathLike] = DEFAULT_ANALYSIS_OUTPUT_FILE,
    preferred_model: Optional[str] = None,
    title: str = "Day 10 Nmap LLM Analysis",
) -> Tuple[str, str]:
    """Analyze a scan JSON file and optionally save the Markdown output."""
    scan_data = load_scan_data(input_file)
    model, analysis = generate_nmap_analysis(scan_data, preferred_model=preferred_model)

    if output_file:
        output_path = Path(output_file)
        output = f"# {title}\n\nModel: `{model}`\n\n{analysis}\n"
        output_path.write_text(output, encoding="utf-8")

        return model, analysis


# ---------------------------------------------------------------------------
# Day 11: Unified, provider-agnostic analysis entry point
# ---------------------------------------------------------------------------
def analyze_scan_data(
    scan_data: dict,
    provider: LLMProvider = LLMProvider.GEMINI,
    preferred_model: Optional[str] = None,
    mode: PromptMode = PromptMode.STANDARD,
    retries: int = 2,
    timeout_ms: int = GEMINI_REQUEST_TIMEOUT_MS,
    api_key: Optional[str] = None,
) -> ScanAnalysisResult:
    """Analyze scan data with a pluggable provider.

    Currently only Gemini is wired up (Day 11), but the signature is designed
    so Day 12 (Ollama) and Day 13 (--llm switcher) can extend the dispatch
    without changing callers.

    Args:
        scan_data: structured scan dict.
        provider: LLM to use (default Gemini).
        preferred_model: model name to try first.
        mode: prompt template to use (STANDARD/BEGINNER/REMEDIATION).
        retries: per-model retry count for transient errors.
        timeout_ms: per-request timeout in milliseconds.
        api_key: explicit API key override; falls back to env/default provider.

    Returns:
        ScanAnalysisResult with provider, model, analysis, prompt, usage.
    """
    prompt = build_prompt(scan_data, mode=mode)

    if provider is LLMProvider.GEMINI:
        model, analysis, usage = _call_gemini(
            prompt=prompt,
            preferred_model=preferred_model,
            retries=retries,
            timeout_ms=timeout_ms,
            api_key=api_key,
        )
    elif provider is LLMProvider.OLLAMA:
        # Placeholder for Day 12: Ollama uses a different HTTP path.
        raise NotImplementedError(
            "Ollama provider support is planned for Day 12."
        )
    else:
        raise NotImplementedError(
            f"Provider '{provider.value}' integration is pending. "
            "Gemini and (soon) Ollama are supported."
        )

    return ScanAnalysisResult(
        provider=provider,
        model=model,
        analysis=analysis,
        prompt=prompt,
        usage=usage,
    )


def _call_gemini(
    prompt: str,
    preferred_model: Optional[str] = None,
    retries: int = 2,
    timeout_ms: int = GEMINI_REQUEST_TIMEOUT_MS,
    api_key: Optional[str] = None,
) -> Tuple[str, str, dict]:
    """Call Gemini with provider-specific config. Returns (model, text, usage)."""
    load_dotenv()
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to .env before running analysis."
        )

    check_gemini_network()
    force_ipv4_resolution()

    client = genai.Client(
        api_key=key,
        http_options=types.HttpOptions(timeout=timeout_ms),
    )

    safety_settings = [
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        ),
    ]

    errors: list = []

    for model in default_models_for_provider(LLMProvider.GEMINI):
        if preferred_model and model != preferred_model:
            # still allow preferred to go first via _model_candidates semantics,
            # but here we rely on default_models_for_provider ordering.
            pass
        for attempt in range(retries + 1):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        safety_settings=safety_settings,
                    ),
                )
                usage = {
                    "candidates": getattr(response.usage_metadata, "candidates", None)
                    if response.usage_metadata
                    else None,
                    "tokens": getattr(response.usage_metadata, "total_token_count", None)
                    if response.usage_metadata
                    else None,
                }
                return model, response.text, usage
            except Exception as exc:
                status = getattr(exc, "code", None) or getattr(
                    exc, "status_code", None
                )
                reason = f"{model} (attempt {attempt + 1}): {exc}"
                errors.append(reason)
                is_retryable = status in RETRYABLE_STATUS or isinstance(
                    exc, TimeoutError
                )
                if attempt < retries and is_retryable:
                    backoff = 5 * (2 ** attempt)
                    print(f"[*] Retrying {model} in {backoff}s after: {exc}")
                    time.sleep(backoff)

    raise RuntimeError(
        "All Gemini model attempts failed:\n" + "\n".join(errors)
    )

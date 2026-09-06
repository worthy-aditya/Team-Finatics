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

import requests
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Day 24: retry notices go through the shared Rich console so they render
# cleanly above the CLI spinner instead of interleaving raw prints.
from sentinelai.ui import info as ui_info


DEFAULT_SCAN_INPUT_FILE = Path("scan_results.json")
DEFAULT_ANALYSIS_OUTPUT_FILE = Path("day9_nmap_llm_analysis.md")

# Day 15 (Week 3): Windows Event Log analysis artifacts. The event-log JSON
# schema is: {"source", "host", "collected_at", "count", "events": [...]},
# where each event carries event_id, timestamp, level, channel, account,
# domain, logon_type, source_ip, message, and an optional count (see
# day15_sample_events.json for the exact contract Affan's parser must match).
DEFAULT_EVENT_LOG_INPUT_FILE = Path("event_logs.json")
DEFAULT_EVENT_LOG_ANALYSIS_OUTPUT_FILE = Path("day15_analysis_events.md")

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


def _gemini_rate_limit_hint(errors) -> str:
    """Append an actionable hint when the failure pattern is free-tier limiting."""
    joined = "\n".join(str(e) for e in errors)
    if "429" in joined or "RESOURCE_EXHAUSTED" in joined or "quota" in joined.lower():
        return (
            "\nHint: this looks like Gemini free-tier rate limiting (429/quota). "
            "Wait ~60s and retry, or switch providers with --llm ollama."
        )
    return ""

GEMINI_API_HOST = "generativelanguage.googleapis.com"

# Ollama (Day 12): local server, no API key required. Override the host via
# OLLAMA_HOST if the server runs on another machine/port.
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
# Local models can be slow on CPU-only machines; allow up to 10 minutes.
OLLAMA_REQUEST_TIMEOUT_S = 600
DEFAULT_OLLAMA_MODELS = ["llama3", "llama3.1", "gemma4"]
# Generation ceiling for /api/generate (tokens to predict) and context window.
# gemma4 defaults to num_ctx=4096 TOTAL (prompt + output), so long
# multi-section analyses (Nmap or Event Log) get cut off mid-sentence with
# done_reason="length" ~2000 tokens in. 6144 is accepted by every local model
# we use (8192 was rejected by gemma4), leaving room for comfortable output.
# Override via OLLAMA_NUM_CTX / OLLAMA_NUM_PREDICT. (Day 15 lesson.)
OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "6144"))
OLLAMA_NUM_PREDICT = int(os.getenv("OLLAMA_NUM_PREDICT", "4096"))


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


# Providers wired up and usable today. OpenAI/Claude are paid-API integrations
# planned for a later sprint day; Gemini (free tier) and Ollama (local) are the
# free options the team uses right now (Days 9-12).
ACTIVE_PROVIDERS = {LLMProvider.GEMINI, LLMProvider.OLLAMA}


def resolve_provider(name: str) -> LLMProvider:
    """Map a CLI/provider name to an LLMProvider enum member.

    Raises a friendly RuntimeError for unknown names and for known-but-pending
    providers (openai/claude), pointing users at the free alternatives.
    """
    try:
        provider = LLMProvider(str(name).strip().lower())
    except ValueError:
        valid = ", ".join(p.value for p in LLMProvider)
        raise RuntimeError(
            f"Unknown LLM provider '{name}'. Valid providers: {valid}."
        )
    if provider not in ACTIVE_PROVIDERS:
        free = ", ".join(sorted(p.value for p in ACTIVE_PROVIDERS))
        raise RuntimeError(
            f"LLM provider '{provider.value}' is not wired up yet (paid API, "
            f"planned for a later sprint day). Currently available FREE "
            f"providers: {free}."
        )
    return provider


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
    # Day 23 review fix: "gemini-2.0-flash" was retired by Google (404), so
    # every Gemini analysis wasted its first attempt. Use the stable alias;
    # the rest of the chain is DEFAULT_GEMINI_MODELS (GEMINI_MODEL env wins).
    LLMProvider.GEMINI: "gemini-flash-latest",
    LLMProvider.OLLAMA: "llama3",
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

# Day 15 (Week 3): Windows Event Log analysis template. Mirrors the proven
# 5-section structure of the Nmap prompt but is driven by Windows Security
# event data (Event IDs such as 4624 logon, 4625 failed logon, 4720 user
# created, 4672 special privileges, 1102 audit log cleared). Strictly
# evidence-based: the model must derive every claim from the events list and
# must not invent events.
EVENT_LOG_ANALYSIS_PROMPT = """
You are a senior Windows security analyst assistant helping a student understand
the security implications of Windows Security event logs. Your analysis must be
strictly evidence-based: base every conclusion only on the event data provided,
and never claim a compromise or an attack occurred unless the events support it
(e.g., correlate multiple 4625 failed logons with a later 4624 success before
calling it a successful intrusion attempt).

IMPORTANT CONTEXT: You are assisting with DEFENSIVE security education and
hardening of the user's own computer or lab environment. The event log data
below was collected as part of a learning exercise or authorized assessment.
Focus on understanding, risk awareness, and remediation. Do NOT provide
step-by-step exploitation instructions, attack playbooks, or specific exploit
commands. Frame everything from a defender's perspective.

Below is structured Windows Security Event Log data (JSON):

{event_log_data}

Produce a Markdown analysis with EXACTLY these sections, in this order:

## 1. Plain-English Summary
A short, beginner-friendly overview: which host the events come from, the time
window covered, how many events were examined, which Security event IDs appear,
and the overall picture in one or two sentences.

## 2. Security Events (ranked by risk)
For EACH distinct security-relevant event ID, provide a structured finding:
- **Event #N - <description> (Event ID <id>)**
  - Severity: <Critical|High|Medium|Low|Info> (score out of 10)
  - Evidence from log: event_id, timestamp(s), account, logon_type, source_ip
    exactly as reported
  - Why it matters: plain-English explanation tied to the event ID and context
    (e.g., 4625 = failed logon, possible brute force; 4720 = new user account
    created, possible persistence; 1102 = audit log cleared, anti-forensics)
Rank every finding from highest to lowest severity. Weigh COUNT and frequency:
a burst of repeated failed logons is riskier than a single occurrence. If only
routine/informational events exist, say so clearly and do not invent risk.

## 3. What These Events Suggest
- For DEFENSIVE awareness only: what a security analyst would infer from the
  event mix (e.g., brute-force pattern, new account + privilege grants, clean
  log), WITHOUT providing an attack walkthrough.
- Correlate related events (4625 failures followed by a 4624 success from the
  same source, 4720 new account plus 4672 special privileges) and state plainly
  what the combination suggests a defender should check.
- Clearly state what the logs PROVE and what they DO NOT prove (logs can show a
  failed logon, but not the attacker's intent or whether a payload executed).

## 4. Recommended Next Steps
Split into two numbered groups, each tied to the specific events it addresses:
### Immediate (investigation)
Steps, tools, or commands a defender can run right now to confirm or rule out
the suspicious activity (e.g., enumerate other logons from that source IP,
inspect account changes, query via PowerShell Get-WinEvent or Event Viewer).
### Medium-term (hardening)
Concrete hardening actions for the specific scenario (account lockout / brute
force policy, review and trim privileged-group memberships, enable additional
auditing, restrict the source, enforce MFA). Reference standard Windows
security guidance, but do not invent URLs.

## 5. Confidence & Limitations
- What this analysis is based on (event IDs, counts, source IPs, time window).
- What could degrade confidence (truncated sample, cleared or missing events,
  a single snapshot without history, spoofable fields such as source IP).
- What is NOT covered and who should verify it (other log channels, antivirus,
  network evidence).

Do not fabricate events that are not present in the event log data. Keep it
concise and actionable.
"""

# Day 17 (Week 3): Remediation variant for Windows Event Log analysis. Mirrors
# the structure of NMAP_REMEDIATION_PROMPT (Day 11) but is driven by Windows
# Security event data. Turns a Day 15/16 finding (e.g. 1102 audit-log clear,
# 4720 backdoor-account creation, a 4625->4624 brute force) into a prioritized,
# evidence-tied fix-it list that a defender can actually execute.
EVENT_LOG_REMEDIATION_PROMPT = """
You are a practical Windows security engineer. Given the Security event log
data below, produce a defensive, action-oriented remediation plan. Keep it
strictly evidence-based: derive every recommendation only from the events
listed, and never invent events or findings that are not present.

IMPORTANT CONTEXT: The data was collected for a learning exercise or an
authorized assessment of the user's own system/lab. Focus on verification and
hardening. Do NOT provide step-by-step exploitation instructions, attack
playbooks, or specific exploit commands. No external URLs.

Below is structured Windows Security Event Log data (JSON):

{event_log_data}

Produce a Markdown remediation plan with these sections, in this order. Tie
every recommendation to the specific event ID(s) that justify it:

## 1. Executive Summary
One short paragraph: which host this covers, how many distinct events need
attention, and the single most important immediate action a defender should take.

## 2. Prioritized Action List
For EACH security-relevant event ID, produce a remediation card. Rank cards from
highest to lowest priority (audit-log clearing and new privileged accounts rank
above a single routine logon):
- **Finding #N - <description> (Event ID <id>)**
  - Risk rating: <High|Medium|Low> — and in one sentence why this event matters
  - Verify now: 1-2 concrete diagnostic steps a defender can run right now
    (e.g. `Get-WinEvent -Id 1102` to check for further log clears, inspect the
    account-creation source host, enumerate logons from the suspect IP).
    Reference the Event ID explicitly so it is tied to the evidence.
  - Fix: concrete hardening steps (disable the suspect account, force password
    reset, enable/expand auditing, restrict source IPs, enforce account
    lockout and MFA). Reference standard guidance (e.g. "CIS Windows Benchmark",
    "NIST 800-63B") but do not invent URLs.
  - Reference: the Event ID(s) and source IP / account this card is based on.

## 3. Compliance Cross-Check
Map each event card to the most relevant framework control where a clear match
exists (e.g. 1102 audit-log clearing -> auditing/retention controls; 4720
account creation + 4672 special privileges -> privileged-account management;
4625 brute force -> account-lockout / MFA). If an event does not clearly map to
a control, say so rather than forcing a match. One line per card.

## 4. Verification Plan
A short checklist a defender can use AFTER remediation to confirm the fix
worked (e.g. re-run `Get-WinEvent -Id 1102` to confirm no further clears,
confirm `backupadmin` is disabled/removed, watch 192.168.1.54 for new 4625s,
re-check privileged-group memberships). Do not fabricate checks the data does
not support.

Do not fabricate findings not present in the event log data. Keep it concise
and actionable.
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


def build_event_log_prompt(
    event_log_data: dict, mode: PromptMode = PromptMode.STANDARD
) -> str:
    """Build a Windows Event Log analysis prompt (Day 15/17).

    Formats structured Security event log JSON into an event-log prompt variant.
    STANDARD (5-section risk report, Day 15) and REMEDIATION (Day 17
    prioritized fix-it plan) are supported. BEGINNER raises a clear error
    instead of silently reusing the Nmap templates on event data (lands later
    in Week 3).

    Args:
        event_log_data: structured event log dict following the contract in
            day15_sample_events.json:
            {"source", "host", "collected_at", "count", "events": [{...}]}.
        mode: prompt template to use (default STANDARD; REMEDIATION available).
    """
    # Compact separators: the JSON payload is reference context, not the
    # analysis — indenting it costs several hundred tokens of context that
    # otherwise limit how long the generated analysis can be.
    # Day 23 review fix: fail fast and clearly when the input is not the
    # event-log schema instead of silently prompting with a malformed payload.
    if not isinstance(event_log_data, dict) or not isinstance(
        event_log_data.get("events"), list
    ):
        raise ValueError(
            "Expected Windows event-log schema JSON (an object with an 'events' "
            "list), e.g. from `sentinelai parse --logs`, `sentinelai logs -o "
            "events.json`, or day15_sample_events.json. Got: "
            f"{type(event_log_data).__name__}."
        )

    compact_json = json.dumps(event_log_data, separators=(",", ":"))
    if mode is PromptMode.STANDARD:
        return EVENT_LOG_ANALYSIS_PROMPT.format(event_log_data=compact_json)
    if mode is PromptMode.REMEDIATION:
        return EVENT_LOG_REMEDIATION_PROMPT.format(event_log_data=compact_json)
    # BEGINNER (and any other future mode) -> explicit error, never silently
    # reuse the standard template on event data. Beginner lands later Week 3.
    raise ValueError(
        f"Event Log prompt mode '{mode.value}' is not built yet. "
        "The 'standard' and 'remediation' event-log variants are available; "
        "the 'beginner' variant arrives later in Week 3."
    )


PathLike = Union[str, Path]


def load_scan_data(path: PathLike = DEFAULT_SCAN_INPUT_FILE) -> dict:
    """Load structured scan data from a JSON file."""
    scan_path = Path(path)
    if not scan_path.exists():
        raise FileNotFoundError(f"Missing scan input file: {scan_path}")

    with scan_path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def load_event_log_data(path: PathLike = DEFAULT_EVENT_LOG_INPUT_FILE) -> dict:
    """Load structured Windows Event Log data from a JSON file (Day 15)."""
    event_path = Path(path)
    if not event_path.exists():
        raise FileNotFoundError(f"Missing event log input file: {event_path}")

    # Day 23: utf-8-sig transparently handles Windows writers that prepend a
    # BOM (Out-File, Notepad, Event Viewer exports) -> no hard failure.
    with event_path.open("r", encoding="utf-8-sig") as f:
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
                    ui_info(f"Retrying {model} in {backoff}s after: {exc}")
                    time.sleep(backoff)

    raise RuntimeError(
        "All Gemini model attempts failed:\n" + "\n".join(errors)
        + _gemini_rate_limit_hint(errors)
    )


def analyze_scan_file(
    input_file: PathLike = DEFAULT_SCAN_INPUT_FILE,
    output_file: Optional[PathLike] = DEFAULT_ANALYSIS_OUTPUT_FILE,
    preferred_model: Optional[str] = None,
    title: str = "Day 10 Nmap LLM Analysis",
    provider: LLMProvider = LLMProvider.GEMINI,
    mode: PromptMode = PromptMode.STANDARD,
) -> Tuple[str, str]:
    """Analyze a scan JSON file with the given provider and save Markdown.

    Day 13: routes through the unified analyze_scan_data() so --llm can pick
    gemini (cloud) or ollama (local) without changing callers. Day 17 threads
    the chosen mode (STANDARD/BEGINNER/REMEDIATION) through to analyze_scan_data.
    """
    scan_data = load_scan_data(input_file)
    result = analyze_scan_data(
        scan_data, provider=provider, preferred_model=preferred_model, mode=mode
    )

    if output_file:
        output_path = Path(output_file)
        output = (
            f"# {title}\n\n"
            f"Provider: {result.provider.value} | Model: `{result.model}`\n\n"
            f"{result.analysis}\n"
        )
        output_path.write_text(output, encoding="utf-8")

    return result.model, result.analysis


# ---------------------------------------------------------------------------
# Day 11: Unified, provider-agnostic analysis entry point
# ---------------------------------------------------------------------------
def analyze_scan_data(
    scan_data: dict,
    provider: LLMProvider = LLMProvider.GEMINI,
    preferred_model: Optional[str] = None,
    mode: PromptMode = PromptMode.STANDARD,
    retries: int = 2,
    timeout_ms: Optional[int] = None,
    api_key: Optional[str] = None,
) -> ScanAnalysisResult:
    """Analyze scan data with a pluggable provider.

    Supports Gemini (cloud) and Ollama (local). The signature is designed so
    Day 13 (--llm switcher / OpenAI / Claude) can extend the dispatch without
    changing callers.

    Args:
        scan_data: structured scan dict.
        provider: LLM to use (default Gemini; OLLAMA for local/private mode).
        preferred_model: model name to try first.
        mode: prompt template to use (STANDARD/BEGINNER/REMEDIATION).
        retries: per-model retry count for transient errors.
        timeout_ms: per-request timeout in milliseconds; None picks a
            provider-aware default (300s Gemini, 600s Ollama — local models
            can take minutes to load from disk on first use).
        api_key: explicit API key override (ignored by Ollama); otherwise the
            provider default env var is used.

    Returns:
        ScanAnalysisResult with provider, model, analysis, prompt, usage.
    """
    prompt = build_prompt(scan_data, mode=mode)

    # Provider-aware default timeouts: local Ollama models may need minutes
    # just to load weights into memory on first use (Day 12 lesson).
    if timeout_ms is None:
        timeout_ms = (
            OLLAMA_REQUEST_TIMEOUT_S * 1000
            if provider is LLMProvider.OLLAMA
            else GEMINI_REQUEST_TIMEOUT_MS
        )

    if provider is LLMProvider.GEMINI:
        model, analysis, usage = _call_gemini(
            prompt=prompt,
            preferred_model=preferred_model,
            retries=retries,
            timeout_ms=timeout_ms,
            api_key=api_key,
        )
    elif provider is LLMProvider.OLLAMA:
        # Day 12: Ollama runs a local HTTP server (default localhost:11434);
        # no API key needed. api_key is accepted but ignored.
        model, analysis, usage = _call_ollama(
            prompt=prompt,
            preferred_model=preferred_model,
            retries=retries,
            timeout_s=max(timeout_ms // 1000, 60),
        )
    else:
        raise NotImplementedError(
            f"Provider '{provider.value}' integration is pending. "
            "Gemini and Ollama are supported."
        )

    return ScanAnalysisResult(
        provider=provider,
        model=model,
        analysis=analysis,
        prompt=prompt,
        usage=usage,
    )


# ---------------------------------------------------------------------------
# Day 15 (Week 3): Windows Event Log analysis — same provider plumbing as the
# Nmap flow, driven by the event-log prompt template. Affan's `--logs` parser
# will feed structured event JSON here; the sample file (day15_sample_events.json)
# lets this run end-to-end before the real parser lands.
# ---------------------------------------------------------------------------
def analyze_event_log_data(
    event_log_data: dict,
    provider: LLMProvider = LLMProvider.GEMINI,
    preferred_model: Optional[str] = None,
    mode: PromptMode = PromptMode.STANDARD,
    retries: int = 2,
    timeout_ms: Optional[int] = None,
    api_key: Optional[str] = None,
) -> ScanAnalysisResult:
    """Analyze Windows Event Log data with a pluggable provider.

    Mirrors analyze_scan_data() for the event-log template, so gemini (cloud
    free tier) and ollama (local/private) work identically for log analysis.

    Args:
        event_log_data: structured event log dict (see build_event_log_prompt).
        provider: LLM to use (default Gemini; OLLAMA for local/private mode).
        preferred_model: model name to try first.
        mode: prompt template to use (only STANDARD on Day 15).
        retries: per-model retry count for transient errors.
        timeout_ms: per-request timeout in milliseconds; None picks a
            provider-aware default (300s Gemini, 600s Ollama).
        api_key: explicit API key override (ignored by Ollama).

    Returns:
        ScanAnalysisResult with provider, model, analysis, prompt, usage.
    """
    prompt = build_event_log_prompt(event_log_data, mode=mode)

    if timeout_ms is None:
        timeout_ms = (
            OLLAMA_REQUEST_TIMEOUT_S * 1000
            if provider is LLMProvider.OLLAMA
            else GEMINI_REQUEST_TIMEOUT_MS
        )

    if provider is LLMProvider.GEMINI:
        model, analysis, usage = _call_gemini(
            prompt=prompt,
            preferred_model=preferred_model,
            retries=retries,
            timeout_ms=timeout_ms,
            api_key=api_key,
        )
    elif provider is LLMProvider.OLLAMA:
        model, analysis, usage = _call_ollama(
            prompt=prompt,
            preferred_model=preferred_model,
            retries=retries,
            timeout_s=max(timeout_ms // 1000, 60),
        )
    else:
        raise NotImplementedError(
            f"Provider '{provider.value}' integration is pending. "
            "Gemini and Ollama are supported."
        )

    return ScanAnalysisResult(
        provider=provider,
        model=model,
        analysis=analysis,
        prompt=prompt,
        usage=usage,
    )


def analyze_event_log_file(
    input_file: PathLike = DEFAULT_EVENT_LOG_INPUT_FILE,
    output_file: Optional[PathLike] = DEFAULT_EVENT_LOG_ANALYSIS_OUTPUT_FILE,
    preferred_model: Optional[str] = None,
    title: str = "Day 15 Event Log LLM Analysis",
    provider: LLMProvider = LLMProvider.GEMINI,
    mode: PromptMode = PromptMode.STANDARD,
) -> Tuple[str, str]:
    """Analyze an event log JSON file with the given provider, save Markdown.

    Routes through analyze_event_log_data() so --llm can pick gemini (cloud)
    or ollama (local) without changing callers.
    """
    event_log_data = load_event_log_data(input_file)
    result = analyze_event_log_data(
        event_log_data, provider=provider, preferred_model=preferred_model, mode=mode
    )

    if output_file:
        output_path = Path(output_file)
        output = (
            f"# {title}\n\n"
            f"Provider: {result.provider.value} | Model: `{result.model}`\n\n"
            f"{result.analysis}\n"
        )
        output_path.write_text(output, encoding="utf-8")

    return result.model, result.analysis


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

    # Day 23 review fix: honor --model / preferred_model. Previously this
    # iterated default_models_for_provider() and ignored preferred_model, so
    # the preferred model was never tried first (and the retired
    # gemini-2.0-flash was tried before the live fallback chain).
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
                usage_meta = getattr(response, "usage_metadata", None)
                usage = {
                    "candidates": getattr(usage_meta, "candidates", None),
                    "tokens": getattr(usage_meta, "total_token_count", None),
                }
                try:
                    text = response.text
                except Exception as exc:
                    raise RuntimeError(
                        f"{model}: response had no readable text ({exc})"
                    ) from exc
                if not (text or "").strip():
                    # Day 23 review fix: never save an empty Markdown report.
                    # Raised inside the retry loop so it is treated as a
                    # non-retryable error and the next model candidate is tried.
                    raise RuntimeError(
                        f"{model}: Gemini returned an empty response "
                        "(blocked or no generated content)."
                    )
                return model, text, usage
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
                    ui_info(f"Retrying {model} in {backoff}s after: {exc}")
                    time.sleep(backoff)

    raise RuntimeError(
        "All Gemini model attempts failed:\n" + "\n".join(errors)
        + _gemini_rate_limit_hint(errors)
    )


# ---------------------------------------------------------------------------
# Day 12: Ollama provider — local models, private/offline mode
# ---------------------------------------------------------------------------
def check_ollama_server(timeout: int = 5) -> dict:
    """Verify the local Ollama server is reachable; return its /api/tags payload."""
    try:
        resp = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(
            f"Cannot reach Ollama server at {OLLAMA_HOST}. "
            "Is Ollama installed and running? Start it with 'ollama serve' "
            "(or any ollama command) and pull a model first, e.g. "
            "'ollama pull llama3'. This is a local-server issue, not a prompt issue."
        ) from exc


def list_ollama_models() -> List[str]:
    """Return model names available on the local Ollama server."""
    payload = check_ollama_server()
    names = []
    for entry in payload.get("models", []):
        name = entry.get("name") or entry.get("model")
        if name and name not in names:
            names.append(name)
    return names


def _ollama_model_candidates(preferred_model: Optional[str] = None) -> List[str]:
    """Build the Ollama model candidate order: explicit → env → installed → defaults."""
    candidates: List[str] = []
    for model in (
        preferred_model,
        os.getenv("OLLAMA_MODEL"),
        *list_ollama_models(),
        *DEFAULT_OLLAMA_MODELS,
    ):
        if model and model not in candidates:
            candidates.append(model)
    return candidates


def _call_ollama(
    prompt: str,
    preferred_model: Optional[str] = None,
    retries: int = 1,
    timeout_s: int = OLLAMA_REQUEST_TIMEOUT_S,
) -> Tuple[str, str, dict]:
    """Call the local Ollama /api/generate endpoint. Returns (model, text, usage).

    Tries candidate models in order; a 404 (model not pulled) advances to the
    next candidate, while transient failures honor the retry counter.
    """
    candidates = _ollama_model_candidates(preferred_model)
    if not candidates:
        raise RuntimeError(
            "No Ollama models available. Pull one first, e.g. 'ollama pull llama3'."
        )

    errors: list = []
    for model in candidates:
        for attempt in range(retries + 1):
            try:
                resp = requests.post(
                    f"{OLLAMA_HOST}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        # Lift the output ceiling so long analyses complete;
                        # num_ctx must also grow or generation stops early at
                        # the default 4096-token window (context + output).
                        "options": {
                            "num_predict": OLLAMA_NUM_PREDICT,
                            "num_ctx": OLLAMA_NUM_CTX,
                        },
                    },
                    timeout=timeout_s,
                )
                if resp.status_code == 404:
                    # Model not pulled locally — advance to the next candidate.
                    errors.append(f"{model}: not found on Ollama server (404)")
                    break
                resp.raise_for_status()
                try:
                    data = resp.json()
                except ValueError as exc:
                    # Day 23 review fix: Ollama always returns JSON; a proxy or
                    # error page would otherwise raise a confusing traceback.
                    # Treat the candidate as failed and move on.
                    errors.append(
                        f"{model}: Ollama returned a non-JSON response ({exc})"
                    )
                    break
                usage = {
                    "prompt_tokens": data.get("prompt_eval_count"),
                    "response_tokens": data.get("eval_count"),
                    "total_duration_ms": (data.get("total_duration") or 0) / 1e6,
                }
                return model, data.get("response", ""), usage
            except requests.exceptions.RequestException as exc:
                reason = f"{model} (attempt {attempt + 1}): {exc}"
                errors.append(reason)
                if attempt < retries:
                    backoff = 5 * (2 ** attempt)
                    ui_info(f"Retrying Ollama {model} in {backoff}s after: {exc}")
                    time.sleep(backoff)

    raise RuntimeError("All Ollama model attempts failed:\n" + "\n".join(errors))

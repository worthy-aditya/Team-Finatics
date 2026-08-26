"""
llm_analyzer.py

Generates a natural-language analysis summary for a set of mapped security
findings (each containing a keyword, its OWASP category, and/or its MITRE
technique).

Two backends:
  1. Gemini API (real AI-generated analysis) — used automatically when
     the GEMINI_API_KEY environment variable is set.
  2. Rule-based fallback — deterministic, offline, no API key required.
     Used automatically if no API key is set, or if the Gemini call fails
     for any reason (network issue, quota, etc.) so the pipeline never
     breaks just because the AI backend is unavailable.

SECURITY NOTE: the API key is read from the environment variable
GEMINI_API_KEY. It is never hardcoded here and must never be committed
to the repository. Set it locally with:

    Windows (PowerShell):  $env:GEMINI_API_KEY = "your-key-here"
    macOS/Linux:            export GEMINI_API_KEY="your-key-here"

Or store it in a local ".env" file that is listed in .gitignore.
"""

import os
import sys

# Confirmed via a live 404 response from the Gemini API itself (which
# explicitly instructed switching to this model), since Google periodically
# retires older model versions. Can still be overridden via the
# GEMINI_MODEL environment variable if this changes again in the future.
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
GEMINI_API_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)


def _describe_finding(finding):
    """
    Build a one-line human-readable description of a single mapped finding.
    Used both as input context for the Gemini prompt and by the rule-based
    fallback.

    Args:
        finding (dict): {"keyword": str, "owasp": dict|None, "mitre": dict|None}

    Returns:
        str: A single descriptive sentence about this finding.
    """
    keyword = finding.get("keyword", "unknown")
    owasp = finding.get("owasp")
    mitre = finding.get("mitre")

    parts = [f"Finding '{keyword}':"]

    if owasp:
        parts.append(f"classified under OWASP {owasp['rank']} ({owasp['name']}).")
    else:
        parts.append("no direct OWASP Top 10:2025 category matched.")

    if mitre:
        parts.append(
            f"Corresponds to MITRE ATT&CK technique {mitre['id']} "
            f"({mitre['name']}) in the {mitre['domain']} matrix."
        )
    else:
        parts.append("No corresponding MITRE ATT&CK technique matched.")

    return " ".join(parts)


def _rule_based_summary(findings):
    """
    Deterministic, offline, rule-based analysis. Used as a fallback when
    no Gemini API key is configured, or if the API call fails.

    Args:
        findings (list[dict]): List of mapped findings.

    Returns:
        str: A multi-line plain-text analysis summary.
    """
    if not findings:
        return "No findings were provided; no analysis could be generated."

    lines = [
        f"Analysis Summary: {len(findings)} finding(s) reviewed.",
        "",
    ]

    owasp_hits = sum(1 for f in findings if f.get("owasp"))
    mitre_hits = sum(1 for f in findings if f.get("mitre"))

    lines.append(
        f"{owasp_hits}/{len(findings)} finding(s) matched an OWASP Top 10:2025 "
        f"category. {mitre_hits}/{len(findings)} finding(s) matched a MITRE "
        f"ATT&CK technique."
    )
    lines.append("")

    for finding in findings:
        lines.append(f"- {_describe_finding(finding)}")

    lines.append("")
    if mitre_hits > 0 or owasp_hits > 0:
        lines.append(
            "Recommendation: review each matched category/technique above and "
            "prioritise remediation for findings with a confirmed MITRE technique, "
            "as these represent known real-world attacker behaviour."
        )
    else:
        lines.append(
            "No findings matched a known category or technique; no immediate "
            "action is indicated based on current mapping data."
        )

    return "\n".join(lines)


def _build_gemini_prompt(findings, audience="general"):
    """
    Build the prompt sent to Gemini, including finding context and an
    audience-appropriate tone instruction.

    Args:
        findings (list[dict]): Mapped findings.
        audience (str): One of "general", "student", "enterprise",
            "red_team", "blue_team", "bug_bounty". Controls tone/depth.

    Returns:
        str: The full prompt text.
    """
    audience_instructions = {
        "student": (
            "Explain each finding clearly for someone learning cybersecurity. "
            "Define any technical terms briefly and explain why each finding matters."
        ),
        "enterprise": (
            "Write a concise, business-appropriate summary suitable for a security "
            "report. Prioritise findings by risk and be direct about impact."
        ),
        "red_team": (
            "Write from an offensive security perspective: note which findings "
            "represent viable attack paths and how they might be chained together."
        ),
        "blue_team": (
            "Write from a defensive/SOC perspective: focus on detection and "
            "triage priority for each finding."
        ),
        "bug_bounty": (
            "Write in a style suitable for a bug bounty report: clear, factual, "
            "and focused on impact and reproducibility."
        ),
        "general": (
            "Write a clear, professional security analysis summary."
        ),
    }
    instruction = audience_instructions.get(audience, audience_instructions["general"])

    finding_lines = "\n".join(f"- {_describe_finding(f)}" for f in findings)

    return (
        f"{instruction}\n\n"
        f"You are analysing the following security findings, each mapped to "
        f"the OWASP Top 10:2025 and/or MITRE ATT&CK frameworks:\n\n"
        f"{finding_lines}\n\n"
        f"Provide a short overall analysis (a few paragraphs) covering: "
        f"what these findings mean together, their relative severity, and "
        f"a brief recommendation."
    )


def _gemini_backed_summary(findings, audience="general"):
    """
    Call the real Gemini API to generate an analysis summary.

    Requires the `requests` library and the GEMINI_API_KEY environment
    variable to be set.

    Args:
        findings (list[dict]): Mapped findings.
        audience (str): Audience mode, see _build_gemini_prompt().

    Returns:
        str: The AI-generated analysis text.

    Raises:
        RuntimeError: If GEMINI_API_KEY is not set, the `requests` library
            is unavailable, or the API call fails for any reason. Callers
            should catch this and fall back to _rule_based_summary().
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is not set.")

    try:
        import requests
    except ImportError as e:
        raise RuntimeError("The 'requests' library is required for Gemini calls.") from e

    prompt = _build_gemini_prompt(findings, audience=audience)

    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }

    try:
        response = requests.post(
            GEMINI_API_URL,
            params={"key": api_key},
            json=payload,
            timeout=45,
        )

        # Prefer explicit status handling so we can include the response
        # body in diagnostics for 4xx/5xx responses (helps debug issues
        # like an invalid model name or auth problem quickly).
        if response.status_code != 200:
            body = response.text or ""
            short_body = body[:1000] + ("..." if len(body) > 1000 else "")
            raise RuntimeError(
                f"Gemini API returned {response.status_code}: {short_body}"
            )

        data = response.json()
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            raise RuntimeError(f"Unexpected Gemini response shape: {data}")

        return text.strip()
    except requests.RequestException as e:
        raise RuntimeError(f"Gemini request failed: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Gemini API call failed: {e}") from e


def analyze_findings(findings, audience="general", use_llm=True):
    """
    Generate a natural-language analysis summary for a list of mapped
    security findings.

    Tries the real Gemini API first (if `use_llm` is True and
    GEMINI_API_KEY is set). Automatically falls back to a deterministic
    rule-based summary if the API key is missing or the API call fails,
    so this function always returns a usable result.

    Args:
        findings (list[dict]): Each item shaped like:
            {"keyword": str, "owasp": dict|None, "mitre": dict|None}
            (this is exactly the shape returned by
            framework_mapper.map_keyword()).
        audience (str): "general", "student", "enterprise", "red_team",
            "blue_team", or "bug_bounty". Only affects Gemini-backed
            output; the rule-based fallback ignores this.
        use_llm (bool): If False, skip Gemini entirely and use the
            rule-based summary (useful for fast/offline tests).

    Returns:
        str: A multi-line analysis summary.

    Example:
        >>> findings = [
        ...     {"keyword": "phishing", "owasp": None,
        ...      "mitre": {"id": "T1566", "name": "Phishing", "domain": "enterprise"}}
        ... ]
        >>> print(analyze_findings(findings, use_llm=False))
        Analysis Summary: 1 finding(s) reviewed.
        ...
    """
    if not findings:
        return "No findings were provided; no analysis could be generated."

    if use_llm:
        try:
            return _gemini_backed_summary(findings, audience=audience)
        except RuntimeError as e:
            # Print diagnostic to stderr so callers running scripts can
            # see why the LLM backend failed, then fall back to the
            # deterministic rule-based summary so the pipeline remains
            # usable regardless.
            print(f"Gemini error: {e}", file=sys.stderr)
            pass

    return _rule_based_summary(findings)


if __name__ == "__main__":
    sample_findings = [
        {
            "keyword": "phishing",
            "owasp": None,
            "mitre": {"id": "T1566", "name": "Phishing", "domain": "enterprise"},
        },
        {
            "keyword": "sql injection",
            "owasp": {"rank": "A05:2025", "name": "Injection"},
            "mitre": None,
        },
    ]
    print("--- Using Gemini if available, else rule-based fallback ---")
    print(analyze_findings(sample_findings))
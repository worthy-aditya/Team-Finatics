"""
remediation_mapper.py

Takes a mapped finding (the same shape produced by
framework_mapper.map_keyword()) and returns concrete, actionable
remediation steps for its OWASP Top 10:2025 category and/or its MITRE
ATT&CK technique.
"""

# Remediation steps keyed by OWASP Top 10:2025 rank.
REMEDIATION_MAP = {
    "A01:2025": [
        "Enforce server-side authorization checks on every request; never rely on client-side checks alone.",
        "Apply the principle of least privilege by default (deny-by-default access control).",
        "Implement object-level and function-level authorization checks (prevent BOLA/BFLA).",
        "Disable directory listing and validate all user-supplied object references.",
        "Log and alert on repeated access-control failures.",
    ],
    "A02:2025": [
        "Remove or disable default accounts, sample apps, and unnecessary features/services.",
        "Automate configuration hardening using a baseline (e.g. CIS Benchmarks) in CI/CD.",
        "Ensure security headers (CSP, X-Content-Type-Options, HSTS) are set correctly.",
        "Restrict cloud storage bucket permissions; audit for public exposure regularly.",
        "Keep environments (dev/staging/prod) consistently configured and patched.",
    ],
    "A03:2025": [
        "Maintain a Software Bill of Materials (SBOM) and monitor dependencies for known CVEs.",
        "Pin dependency versions and verify package integrity (checksums/signatures) before install.",
        "Restrict and audit third-party/CI pipeline permissions and secrets access.",
        "Adopt automated dependency-update tooling (e.g. Dependabot) with review gates.",
        "Vet third-party libraries and build tools before adoption; avoid unmaintained packages.",
    ],
    "A04:2025": [
        "Use strong, up-to-date cryptographic algorithms; retire deprecated ones (MD5, SHA-1, DES).",
        "Encrypt sensitive data at rest and in transit (TLS 1.2+ everywhere).",
        "Store and rotate cryptographic keys/secrets using a dedicated secrets manager, not in code.",
        "Avoid storing sensitive data unnecessarily; apply data minimization.",
        "Ensure passwords are hashed with a modern, salted algorithm (bcrypt/argon2), never plaintext.",
    ],
    "A05:2025": [
        "Use parameterized queries / prepared statements for all database access — never string-concatenate input.",
        "Validate and sanitize all user input on the server side using an allow-list approach.",
        "Use an ORM or query builder that escapes input by default where practical.",
        "Apply context-aware output encoding to prevent XSS alongside injection defenses.",
        "Run static/dynamic analysis (SAST/DAST) to catch injection flaws before release.",
    ],
    "A06:2025": [
        "Incorporate threat modeling into the design phase of every new feature.",
        "Use secure-by-default frameworks and design patterns rather than bolting on security later.",
        "Define and enforce trust boundaries between system components.",
        "Maintain a library of vetted, reusable secure design patterns for common use cases.",
        "Perform security architecture reviews before implementation begins.",
    ],
    "A07:2025": [
        "Enforce multi-factor authentication (MFA) for all accounts, especially privileged ones.",
        "Implement account lockout / rate limiting after repeated failed login attempts.",
        "Use secure, random session identifiers and invalidate sessions on logout/timeout.",
        "Never allow weak or default passwords; enforce a strong password policy.",
        "Monitor and alert on abnormal authentication patterns (e.g. impossible travel, brute force).",
    ],
    "A08:2025": [
        "Verify software and dependency integrity using digital signatures/checksums before use.",
        "Restrict and audit access to CI/CD pipelines; require signed commits where possible.",
        "Avoid insecure deserialization of untrusted data; validate/allow-list expected types.",
        "Use dependency-integrity tools (lockfiles, Sigstore, SLSA provenance) in the build process.",
        "Review third-party plugins/extensions before granting them elevated trust.",
    ],
    "A09:2025": [
        "Log all security-relevant events (auth attempts, access-control failures, input validation failures).",
        "Ensure logs include enough context (timestamp, source IP, user ID) to support investigation.",
        "Set up real-time alerting for suspicious patterns, not just passive log storage.",
        "Protect log integrity — prevent tampering or deletion by attackers covering their tracks.",
        "Establish a defined incident response process tied to alerting triggers.",
    ],
    "A10:2025": [
        "Implement robust error handling that fails securely (fail closed, not open).",
        "Avoid exposing stack traces, debug info, or internal error details to end users.",
        "Add input validation and bounds checking to prevent unexpected crashes.",
        "Test edge cases and malformed input deliberately (fuzz testing) before release.",
        "Ensure exceptions are logged centrally for visibility into recurring failure patterns.",
    ],
}

# Remediation steps keyed by MITRE ATT&CK technique ID.
MITRE_REMEDIATION_MAP = {
    "T1566": [
        "Deploy email authentication (SPF, DKIM, DMARC with a reject policy).",
        "Use email filtering/sandboxing to detect malicious links and attachments before delivery.",
        "Enforce phishing-resistant MFA (e.g. FIDO2/WebAuthn) to limit credential-theft impact.",
        "Run regular, realistic phishing-simulation training for employees.",
        "Provide a simple one-click mechanism for employees to report suspicious emails to the SOC.",
    ],
    "T1059": [
        "Enable script block logging and module logging for command-line interpreters.",
        "Restrict interpreter use via application allow-listing (e.g. AppLocker, WDAC).",
        "Enforce least privilege so standard users cannot run unrestricted scripts.",
        "Monitor for suspicious command-line flags (encoded commands, execution policy bypass).",
        "Disable or tightly control interpreters that aren't needed for business function.",
    ],
    "T1059.001": [
        "Enable PowerShell Script Block Logging (Event ID 4104) and Module Logging, fed into a SIEM.",
        "Enforce PowerShell Constrained Language Mode for non-administrative users.",
        "Apply AppLocker or Software Restriction Policies to control script execution.",
        "Monitor for suspicious flags such as -ExecutionPolicy Bypass or -EncodedCommand.",
        "Upgrade to PowerShell 5+ and enable Antimalware Scan Interface (AMSI) integration.",
    ],
    "T1110": [
        "Enforce account lockout policies after a defined number of failed login attempts.",
        "Implement rate limiting / CAPTCHA on authentication endpoints.",
        "Require MFA so a correctly guessed password alone is not sufficient for access.",
        "Monitor and alert on clusters of failed authentication events from a single source.",
        "Avoid default or commonly-guessed credentials across all accounts and services.",
    ],
    "T1021.004": [
        "Enforce SSH public-key authentication; disable password-based SSH login.",
        "Restrict SSH access to internal management networks or require VPN/jump-host access.",
        "Disable direct root login over SSH.",
        "Monitor SSH logs for anomalous source IPs or login patterns.",
        "Keep SSH server software patched and disable outdated/weak ciphers.",
    ],
}

_GENERIC_MITRE_FALLBACK = [
    "Review the official MITRE ATT&CK mitigation (M-number) guidance for this specific technique.",
    "Apply the principle of least privilege to reduce the blast radius if this technique is used.",
    "Ensure relevant logging/telemetry is enabled to detect this technique's activity.",
]


def _lookup_mitre_remediation(technique_id):
    """
    Look up remediation steps for a MITRE technique ID, falling back to
    the parent technique (by stripping a sub-technique suffix like
    ".001") if the exact ID isn't mapped, and finally to a generic
    fallback if neither is found.

    Args:
        technique_id (str): e.g. "T1059.001" or "T1566".

    Returns:
        list[str]: Remediation steps (never empty — falls back to a
            generic list rather than returning nothing).
    """
    if technique_id in MITRE_REMEDIATION_MAP:
        return MITRE_REMEDIATION_MAP[technique_id]

    parent_id = technique_id.split(".")[0]
    if parent_id in MITRE_REMEDIATION_MAP:
        return MITRE_REMEDIATION_MAP[parent_id]

    return _GENERIC_MITRE_FALLBACK


def get_remediation(finding):
    """
    Return concrete remediation steps for a single mapped finding.

    Args:
        finding (dict | None): Shaped like the output of
            framework_mapper.map_keyword():
            {"keyword": str, "owasp": dict|None, "mitre": dict|None}
            Malformed or missing input is handled gracefully.

    Returns:
        dict: {
            "keyword": <original keyword, or None if unavailable>,
            "owasp_remediation": list[str] | None,
            "mitre_remediation": list[str] | None,
        }
        Both remediation fields are None if the corresponding framework
        had no match in the input finding.

    Example:
        >>> finding = {
        ...     "keyword": "sql injection",
        ...     "owasp": {"rank": "A05:2025", "name": "Injection"},
        ...     "mitre": None,
        ... }
        >>> result = get_remediation(finding)
        >>> result["owasp_remediation"][0]
        'Use parameterized queries / prepared statements for all database access — never string-concatenate input.'
        >>> result["mitre_remediation"] is None
        True
    """
    if not isinstance(finding, dict):
        return {"keyword": None, "owasp_remediation": None, "mitre_remediation": None}

    keyword = finding.get("keyword")
    owasp = finding.get("owasp")
    mitre = finding.get("mitre")

    owasp_remediation = None
    if owasp and isinstance(owasp, dict) and owasp.get("rank"):
        owasp_remediation = REMEDIATION_MAP.get(owasp["rank"], [])

    mitre_remediation = None
    if mitre and isinstance(mitre, dict) and mitre.get("id"):
        mitre_remediation = _lookup_mitre_remediation(mitre["id"])

    return {
        "keyword": keyword,
        "owasp_remediation": owasp_remediation,
        "mitre_remediation": mitre_remediation,
    }


def get_remediation_for_findings(findings):
    """
    Apply get_remediation() to a batch of findings.

    Args:
        findings (list[dict]): List of findings, each shaped like the
            output of framework_mapper.map_keyword().

    Returns:
        list[dict]: One remediation result per input finding, in the
            same order.

    Example:
        >>> findings = [
        ...     {"keyword": "phishing", "owasp": None,
        ...      "mitre": {"id": "T1566", "name": "Phishing", "domain": "enterprise"}}
        ... ]
        >>> results = get_remediation_for_findings(findings)
        >>> len(results)
        1
    """
    if not findings:
        return []
    return [get_remediation(f) for f in findings]


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
        {
            "keyword": "brute force",
            "owasp": {"rank": "A07:2025", "name": "Authentication Failures"},
            "mitre": {"id": "T1110", "name": "Brute Force", "domain": "enterprise"},
        },
    ]

    for result in get_remediation_for_findings(sample_findings):
        print(f"\nKeyword: {result['keyword']}")
        if result["owasp_remediation"]:
            print("  OWASP remediation:")
            for step in result["owasp_remediation"]:
                print(f"    - {step}")
        if result["mitre_remediation"]:
            print("  MITRE remediation:")
            for step in result["mitre_remediation"]:
                print(f"    - {step}")
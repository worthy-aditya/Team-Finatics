# Security and Responsible Use Policy

## Purpose

SentinelAI is a defensive security tooling project for mapping findings to OWASP and MITRE frameworks, summarizing security reports, and supporting authorized assessment workflows. It is intended for legitimate security validation, engineering review, and training in environments where the operator has explicit permission to test.

## Responsible use

Use SentinelAI only when one of the following is true:

- You are testing a system you own or administer.
- You are operating under an explicit written authorization from the system owner.
- You are conducting a controlled lab or training exercise in a safe, isolated environment.

## Explicit boundaries

This project must not be used to:

- scan or attack internet systems without permission
- exfiltrate credentials or sensitive data
- perform destructive actions
- bypass access controls or domain ownership restrictions
- automate unauthorized reconnaissance or exploitation

## Scope of the tool

The repository focuses on:

- keyword-to-OWASP mapping
- keyword-to-MITRE mapping
- report generation and remediation guidance
- consent and domain verification gates for authorized access
- documentation and workflow checks for safe security review

The project does not provide a backdoor, exploit generation framework, credential harvesting capability, or a tool for unauthorized remote intrusion.

## Legal and operational disclaimer

This project is provided for educational and authorized security assessment use only. It does not grant permission to scan or attack any system. The operator is responsible for ensuring all testing is lawful, authorized, and within the scope of the consent they have obtained.

## Required controls before scanning

Before running any active target scan, ensure all of the following are true:

1. explicit consent has been captured and validated
2. the target domain has been checked against the expected ownership domain
3. the target is an approved host or local test environment
4. the workflow is scoped to a controlled test target, not a production customer system
5. the report is used for authorized remediation and review, not for disclosure or exploitation

## Reporting and escalation

If a test reveals a real issue, follow your organization’s reporting procedures. Do not publicize data from an unauthorized target. Use the tool to support remediation, learning, and compliance-driven security work.

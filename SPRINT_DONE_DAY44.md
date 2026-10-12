# Sprint Done — Day 44

## Final milestone condition

A user can run an authorized active scan end-to-end against a controlled local target when:

- the consent gate passes
- domain ownership is verified
- the scan target is approved and in scope
- ZAP active scanning is executed against the approved target
- findings are mapped to OWASP and MITRE
- the LLM explains them in plain English
- the results are presented in a complete report

## Implementation status

This repository supports the controlled workflow required for this milestone through:

- consent validation and domain verification modules
- access and policy gates
- report generation and OWASP/MITRE mapping
- documentation for responsible use and approved workflow

The project is intended to be used in a local, authorized, deliberately vulnerable target environment and not against unapproved systems.

## Safety note

All active scanning must follow the project security policy and ethical-use guidance. The correct operational path is to validate consent, verify ownership, scan only a controlled and approved target, and report findings through the project’s mapping and report-generation pipeline.

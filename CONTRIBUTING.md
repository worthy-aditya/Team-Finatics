# Contributing to SentinelAI

Thank you for helping improve SentinelAI. Contributions should preserve
mapping accuracy, deterministic offline behavior, and the existing public
Python APIs.

## Development Setup

```bash
git clone https://github.com/worthy-aditya/Team-Finatics.git
cd Team-Finatics
python -m venv venv
```

Activate the environment:

```powershell
venv\Scripts\Activate.ps1
```

```bash
source venv/bin/activate
```

Install the project dependencies:

```bash
pip install -r requirements.txt
```

## Before Opening a Pull Request

1. Create a focused branch from `main`.
2. Keep changes limited to one feature, bug fix, or documentation task.
3. Add or update tests for changed behavior.
4. Run the complete suite:

```bash
pytest -v
```

5. Check that no API keys, scan output containing sensitive data, generated
   binaries, or local virtual-environment files are included.
6. Update `README.md`, `USAGE.md`, or architecture documentation when public
   behavior changes.

## Adding Mapping Data

- Preserve the source dataset's naming and identifiers.
- Use the existing OWASP rank and MITRE technique ID formats.
- Add a regression test for every new keyword or mapping rule.
- Avoid changing the meaning of an existing keyword without documenting the
  compatibility impact.

## Pull Requests

A pull request should include:

- A concise title describing the change.
- A summary of the user-visible or developer-visible behavior.
- Test commands and their results.
- Any required configuration, data, or documentation changes.
- Notes about limitations or follow-up work.

Reviewers should confirm that tests pass, inputs are handled safely, secrets are
not exposed, and the change matches the architecture documented in
`ARCHITECTURE.md`.

## Commit Messages

Use concise, imperative commit messages, for example:

```text
Add remediation guidance for OWASP A05
Fix event log keyword extraction
Document report pipeline architecture
```

## Reporting Problems

When reporting a bug, include the operating system, Python version, command
used, expected behavior, actual behavior, and a minimal sanitized reproduction.
Never include API keys or confidential scan data.

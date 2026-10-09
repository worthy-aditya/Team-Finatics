# SentinelAI Demo Narrative

**Prepared:** 2026-10-07  
**Sprint:** Week 7, Day 44  
**Audience:** Mentors, reviewers, cybersecurity learners, and small IT teams  
**Target duration:** 5-7 minutes; actual timing depends on the selected LLM provider and machine.

## Demo Goal

Show SentinelAI's defensive workflow from local security observations to an understandable analysis and report. The primary run uses a loopback scan of the presenter's own machine and the built-in sample event corpus. It does not scan a public or third-party target and does not run ZAP active testing.

## Pre-Demo Checklist

- Open a terminal in the repository root and activate the project venv.
- Confirm `python sentinelai.py --version`, `nmap --version`, and the needed provider are available.
- For the all-local analysis path, start Ollama and confirm the selected model is available with `ollama list`.
- If using Gemini instead, confirm the presenter has configured their provider credentials and is comfortable sending the selected input to that cloud provider.
- Use only `127.0.0.1` for the Nmap scan and `--sample` for event logs.
- Do not run `--active` in this demo. Day 42's live ZAP scan was canceled at the consent gate; do not imply that a live active scan or its findings were demonstrated.
- Close or redact terminal output that contains personal paths, usernames, local network details, or credentials before sharing screenshots.

## Run of Show

### 1. Opening: the job to be done (about 30 seconds)

**Say:**

> "Security data is useful only when people can interpret it and decide what to do next. SentinelAI is a defensive command-line workflow that takes scan or Windows event data, adds structured context, and helps turn observations into a report. It is an analysis aid: a person still checks the evidence and makes the security decision."

**Transition:**

> "I'll show this on my own machine and on a built-in event sample, so no third-party systems or real user logs are involved."

### 2. Scan the presenter's own machine (about 1 minute)

**Run:**

```powershell
python sentinelai.py scan --target 127.0.0.1 --fast --json-file demo_day44_scan.json
```

**Show:** The scan progress and resulting summary. Open the saved JSON only if time permits.

**Say:**

> "This command uses Nmap against loopback on this machine. SentinelAI collects the structured result so it can be reviewed and passed to the analysis step. The exact ports depend on what is running locally; an empty or small result is still a valid observation, not a failure."

**Transition:**

> "Network observations are one input. Next I'll use the sample event corpus to show the same idea with Windows security events."

### 3. Analyze sample Windows events (about 1-2 minutes)

**Run, with local Ollama available:**

```powershell
python sentinelai.py logs --sample --analyze --llm ollama --mode remediation
```

**Show:** The detected event summary and the remediation-oriented analysis. Refer to event IDs and mappings only if they appear in the output.

**Say:**

> "This uses SentinelAI's built-in sample rather than reading this computer's Security log. The pipeline organizes the event observations and produces suggested follow-up. Framework references help give the observation context, while the underlying event evidence remains visible for a person to review."

**Privacy note:**

> "This run uses the local Ollama provider. If we chose a cloud provider, we would first consider whether the input is appropriate to send to that provider and its terms."

### 4. Analyze and export the scan result (about 1-2 minutes)

**Run, with local Ollama available:**

```powershell
python sentinelai.py analyze -i demo_day44_scan.json --kind scan --llm ollama --mode beginner -o demo_day44_analysis.md
python sentinelai.py report -i demo_day44_scan.json -o demo_day44_report --format text
```

**Show:** The Markdown analysis and generated text report. Point out that report contents reflect this machine's actual scan result; do not read an example finding as if it appeared in this run.

**Say:**

> "The same scan data can be explained in a beginner-friendly mode and saved for later review. The report command also produces a conventional artifact. These outputs make the observations easier to share, but the analyst should verify recommendations and framework mappings before acting on them."

### 5. Close: scope and trust (about 30 seconds)

**Say:**

> "SentinelAI brings scan and event observations, analysis options, and reporting into one defensive CLI workflow. It does not replace a scanner, an analyst, or a formal assessment. Active ZAP testing is a separate, authorization-gated capability; today's demo does not run it or claim live ZAP findings."

**Close with:**

> "The goal is to make the next human decision better informed, not to make that decision on the user's behalf."

## Fallbacks

- **Nmap is unavailable or loopback returns no useful services:** use a repository scan JSON fixture that is already present, identify it as a fixture, then run the analysis and report stages against that file.
- **Ollama is unavailable or too slow:** skip the live LLM stage and show a previously generated, clearly labeled analysis artifact. Alternatively use Gemini only if credentials are configured and the presenter approves sending that data to the cloud provider.
- **A command fails:** stop at the failed stage, explain the limitation, and switch to the labeled fixture. Do not invent output or claim an unrun stage succeeded.
- **Any question about scanning an external site:** state that external active testing is out of scope for this demo and requires explicit written authorization.

## Likely Questions

**Does SentinelAI replace Nmap or a SIEM?**  
No. It uses scan and event data as inputs and helps analyze and report them; it is not a replacement for established collection, monitoring, or response systems.

**Can I trust every AI recommendation?**  
No. AI output is decision support. Review it against the underlying evidence and validate any remediation before applying it.

**Does the consent gate prove legal authorization?**  
No. The operator is responsible for obtaining legal authorization. A typed attestation or domain token is not a legal determination.

**Was live ZAP scanning demonstrated?**  
No. Day 42's environment preflight passed, but the operator canceled at the consent prompt before domain verification and before any active ZAP requests.

## Rehearsal Checklist

- [ ] Run every command in order from the repository root.
- [ ] Check the generated filenames and remove stale artifacts before timing a fresh rehearsal.
- [ ] Practice the narration while commands execute; never describe output before it appears.
- [ ] Record actual elapsed time and adjust the estimate above.
- [ ] Confirm the demo uses only loopback and sample events.
- [ ] Keep the Day 42 ZAP limitation visible in slides or Q&A notes.

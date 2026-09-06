# SentinelAI — Demo Narrative & Rehearsal Script

**Target total time: ~4-5 minutes**
Practice out loud with a timer. Adjust pacing once you know your natural speed.

---

## Part 1: The Problem (30 seconds)

> "Security analysts constantly need to answer two questions about any finding:
> what category of risk is this, and what real attacker technique does it map to?
> Today that's a manual lookup process — someone has to know the OWASP Top 10 and
> MITRE ATT&CK well enough to cross-reference them by hand, every time. SentinelAI
> automates that."

---

## Part 2: Live Demo — the mapping (90 seconds)

**[Open terminal, have venv already activated]**

> "Let's say I've run an Nmap scan and found some open services. I feed that
> straight into SentinelAI."

**Run:**
```powershell
python nmap_report_pipeline.py
```

**While it runs, narrate:**

> "Behind the scenes, three things just happened. First, the parser pulled out
> service indicators — here it found 'ssh' and 'powershell'. Second, each of
> those got checked against two frameworks at once: the OWASP Top 10:2025, and
> MITRE ATT&CK — which I'm searching across Enterprise, Mobile, and ICS matrices,
> not just one."

**[Point to the report output]**

> "You can see 'powershell' correctly mapped to T1059.001 — that's a real MITRE
> technique ID, 'Command and Scripting Interpreter: PowerShell', in the enterprise
> matrix. That's not a guess — it's pulled directly from MITRE's own STIX threat
> intelligence data."

---

## Part 3: The AI Analysis Layer (60 seconds)

> "The third thing that happened is analysis. SentinelAI sends the mapped findings
> to Google's Gemini API, which writes a genuine, reasoned security analysis —
> not a template. Watch what it produces."

**[Scroll to the ANALYSIS section]**

> "It's explaining severity, correlating the findings together — SSH plus
> PowerShell suggests remote access paired with post-exploitation capability —
> and giving specific, technically accurate remediation, like enabling PowerShell
> Script Block Logging, Event ID 4104."

**Important honesty point to include:**

> "And critically — if Gemini is unavailable for any reason, the pipeline doesn't
> break. It automatically falls back to a deterministic, rule-based summary, so
> the tool always produces a usable report."

---

## Part 4: Second Input Source — Event Logs (45 seconds)

> "It's not just network scans. SentinelAI also processes security event logs."

**Run:**
```powershell
python event_log_report_pipeline.py
```

> "This one's interesting — it's not just matching literal keywords. If it sees
> three or more failed login events in a row, it *infers* a brute-force pattern,
> even though the log text never contains the words 'brute force'. That maps
> correctly to both OWASP A07 — Authentication Failures — and MITRE T1110."

---

## Part 5: Remediation (30 seconds)

> "Every finding also comes with concrete remediation steps — not generic advice,
> specific to that OWASP category or MITRE technique."

**Run:**
```powershell
python remediation_mapper.py
```

---

## Part 6: Testing & Reliability (30 seconds)

> "All of this is backed by a full automated test suite — 56 tests, covering
> normal cases, edge cases like empty or malformed input, and full end-to-end
> pipeline tests. It's confirmed passing on both Windows and Linux."

**[Optional: run `pytest -v` live if time allows, or just show the final line]**

---

## Closing Line (15 seconds)

> "SentinelAI isn't trying to replace an analyst's judgment — it automates the
> tedious lookup and correlation work, so people can spend their time on the
> decisions that actually need human expertise."

---

## Rehearsal Checklist

- [ ] Run through once silently to check timing
- [ ] Run through once out loud with a stopwatch
- [ ] Time each part separately, note where you're consistently over/under
- [ ] Have a fallback plan if Gemini times out live (mention the fallback IS the demo point — don't panic, just narrate it happening)
- [ ] Pre-open all terminal windows/tabs needed so you're not fumbling mid-demo
- [ ] Know your total time — aim for 4-5 minutes, trim Part 6 first if running long

## Anticipated Questions (prepare short answers)

- **"Why both OWASP and MITRE, not just one?"** — OWASP tells you the risk *category*; MITRE tells you the actual attacker *technique*. Together they give both the "what" and the "how."
- **"What if Gemini gives wrong information?"** — It's an analysis aid, not the source of truth — the underlying OWASP/MITRE mapping is deterministic and dataset-driven; only the narrative explanation is AI-generated.
- **"Does this replace a SOC/pentest tool?"** — No — it's a classification and reporting layer that sits on top of existing tools' output (Nmap, logs), not a scanner itself.
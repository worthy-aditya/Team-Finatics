# Week 2 — Day 10: Refine LLM Prompt — Risk Identification + Next Steps
**Date:** 2026-08-26
**Developer:** Aditya Gupta (Project Lead & LLM)
**Sprint:** SentinelAI 30-Day Sprint | Week 2, Day 10
**Status:** ✅ **COMPLETE**

---

## Day 10 Objective
> Refine the Day 9 analysis prompt — add structured risk identification (severity scores + evidence) and actionable next steps split into Immediate (verification) / Hardening (medium-term)
> **Deliverable:** Refined `NMAP_ANALYSIS_PROMPT` validated against **3 test scans**

---

## What Was Done

### 1. Refined the LLM Prompt
**File Modified:** `sentinelai/prompt_engine.py`

The Day 9 prompt was upgraded from a loose 4-part request to a **strict 5-section Markdown template** the LLM must follow exactly:

| # | Section | What it forces the LLM to produce |
|---|---------|-----------------------------------|
| 1 | **Plain-English Summary** | Target, host status, open ports, services, system type |
| 2 | **Risk Findings (ranked)** | Per-port structured finding: `Severity: <Level> (X/10)`, `Evidence from scan` (exact state/product/version), `Why it matters` |
| 3 | **Attacker Perspective** | Defensive-only: what an attacker infers + NSE audit scripts a *defender* runs |
| 4 | **Recommended Next Steps** | Split into **Immediate (verification)** + **Hardening (medium-term)**, tied to specific services |
| 5 | **Confidence & Limitations** | Strongly-supported vs speculative, plus recommended additional scans/data sources |

Also added **defensive context framing** to the prompt — explicitly stating the work is
defensive/security-education analysis of the owner's own system OR a named public test
target (e.g. `scanme.nmap.org`) and that exploit playbooks must NOT be provided. During
validation this framing was refined: an initial "owner of the scanned systems" version
was correct for private infra but caused Gemini to **refuse** public/hosted targets like
`scanme.nmap.org`; naming both "own system" and "public test targets" plus
`BLOCK_NONE` safety settings eliminated the refusals.

### 2. Reliability Fixes (found during Day 10 validation)
- **IPv4-only resolution patch** (`force_ipv4_resolution()`): the google-genai httpx client hung for minutes on hosts that resolve to both A + AAAA records when the machine has no IPv6 route. Now forces `AF_INET` for Google/`*.ai` hosts → API calls complete in seconds.
- **Longer, explicit timeout** (`GEMINI_REQUEST_TIMEOUT_MS = 300_000`) via `HttpOptions`.
- **Retry with exponential backoff** for transient Gemini errors (429 / 500 / 503 / timeouts).
- **Updated default model list** to currently-valid models: `gemini-3.6-flash`, `gemini-flash-latest`, `gemini-3.5-flash`, `gemini-3.7-flash` (the old `gemini-2.5-flash` / `gemini-2.0-flash` now return 404).
- **Explicit safety settings** (`BLOCK_NONE` for benign harm categories) for the defensive analysis use-case.

### 3. New Test Wrapper
**File Created:** `test_day10_prompt_refinement.py`
- Runs 3 real Nmap scans → exports JSON → pushes each through the refined prompt → saves Markdown
- Resume-safe (skips scans whose JSON already exists)

---

## Test Results ✅ (3 Test Scans)

### Scan 1: Localhost `127.0.0.1`
- **Findings:** 2 open ports — 135/msrpc (Microsoft Windows RPC, 5.5/10), 445/microsoft-ds (SMB, 6.5/10); 137 filtered
- **Analysis:** `day10_analysis_localhost.md` (7031 bytes)

### Scan 2: Public Test Host `scanme.nmap.org`
- **Findings:** 2 open ports — 80/Apache httpd 2.4.7 (Ubuntu, 6.5/10), 22/OpenSSH 6.6.1p1 (Ubuntu, 5.5/10)
- **Analysis:** `day10_analysis_scanme.md` (6953 bytes)

### Scan 3: Local Gateway `172.16.2.1` (ZyXEL ZyWALL)
- **Findings:** 4 open ports — 443/HTTPS ZyXEL config (6.0/10), 80/HTTP (5.0/10), 22/SSH (3.5/10), 53/DNS (3.0/10)
- **Analysis:** `day10_analysis_gateway.md` (8047 bytes)

**All 3 analyses contain all 5 required sections** ✅

---

## Integration Flow (Refined Prompt)

```
Nmap scan (3 targets)
    ↓
scan_results_day10_*.json
    ↓
build_nmap_analysis_prompt() -> 5-section risk-focused template
    ↓
genai.Client(...) with IPv4 patch + timeout + retries + safety settings
    ↓
day10_analysis_*.md           ← Risk #N + Severity X/10 + Evidence + Next Steps
```

---

## Components Working Together

| Component | Status | Notes |
|-----------|--------|-------|
| Refined `NMAP_ANALYSIS_PROMPT` | ✅ | Adds risk IDs, severity scores, split next steps |
| `force_ipv4_resolution()` | ✅ | Fixes google-genai IPv6 hangs on this network |
| `GEMINI_REQUEST_TIMEOUT_MS` | ✅ | 300s explicit per-request timeout |
| Retry + backoff | ✅ | Handles transient 429/500/503 |
| Updated model fallbacks | ✅ | Removed 404 models, valid 2026 list |
| Safety settings | ✅ | Prevents defensive-analysis refusals |
| `test_day10_prompt_refinement.py` | ✅ | 3-scan validation pipeline, resume-safe |

---

## What Changed vs Day 9

| Aspect | Day 9 | Day 10 |
|--------|-------|--------|
| Prompt structure | 4 loose paragraphs | 5 strict Markdown sections |
| Risk identification | "list/highlights" | Ranked `Risk #N` with Severity X/10 + Evidence |
| Next steps | One list | **Immediate (verification)** + **Hardening (medium-term)** |
| Reliability | Could hang / fail on IPv6 + old models | IPv4 patch, 300s timeout, retries, valid models |
| Safety refusals | Possible on real-device scans | Defensive framing + BLOCK_NONE settings |
| Validation | 1 scan (localhost) | **3 test scans** (localhost, public, gateway) |

---

## Ready for Next Step

- **Day 11:** Complete prompt engineering module (reusable functions)
- **Day 12:** Ollama support — local Llama 3 via Ollama
- **Day 13:** LLM switcher — `--llm openai/claude/gemini/ollama` flag

---

## Sign-Off

**Day 10 Status:** ✅ **COMPLETE AND VALIDATED**

- ✅ Refined prompt with risk identification + severity scoring + evidence
- ✅ Next steps split into Immediate/Hardening
- ✅ Validated with 3 real test scans (localhost, public test host, local gateway)
- ✅ Reliability fixes (IPv6 hang, model fallbacks, timeouts, retries)
- ✅ All analyses pass 5-section structure check

**Developer:** Aditya Gupta
**Completion Date:** 2026-08-26
**Team:** Team Finatics | CodeQuest 4.0
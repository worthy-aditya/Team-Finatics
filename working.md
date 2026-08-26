# Working Notes — SentinelAI Week 2 Implementation Log (Days 9–13)

**Team:** Team Finatics | **Developer:** Aditya Gupta (Lead / LLM integration)
**Purpose:** A practical record of *how* each task was implemented (flow +
procedure) and *every problem we hit along the way*, with how each was tackled.
Written to help teammates avoid the same pitfalls and speed up debugging.

---

## 0. The Big Picture — Pipeline We Ended Up With

```
Nmap target
    │  python-nmap wrapper (sentinelai/scanner.py)
    ▼
Structured scan JSON  ──►  exported to disk (scan_results*.json)
    │
    ▼
Prompt engine (sentinelai/prompt_engine.py)
    ├─ load_scan_data()            reads JSON
    ├─ build_prompt(mode=…)        STANDARD / BEGINNER / REMEDIATION templates
    └─ analyze_scan_data(          ONE unified entry point
         provider=…,                 GEMINI (cloud free tier) or OLLAMA (local)
         preferred_model=…,
         mode=…, retries=…, timeout_ms=None)
        │
        ├── _call_gemini()   google-genai SDK + safety settings + retry/backoff
        └── _call_ollama()   local REST /api/generate (requests lib)
         │
         ▼
ScanAnalysisResult (provider, model, analysis text, usage tokens)
    │
    ▼
Markdown report (Provider | Model header + 5-section analysis)
```

CLI surface after Day 13:

```bash
python sentinelai.py scan   --target 127.0.0.1
python sentinelai.py analyze -i scan_results.json --llm ollama   # free/local
python sentinelai.py analyze -i scan_results.json --llm gemini   # free/cloud
```

---

## 1. Day 9 — LLM Analysis via Gemini (first working pipeline)

### What we built
`sentinelai/prompt_engine.py` — the reusable flow *structured Nmap JSON →
prompt → plain-English analysis*.

**Procedure followed:**
1. Defined `NMAP_ANALYSIS_PROMPT`: role setup ("cybersecurity analyst assistant
   helping a student") + 4 loose requests (summary, high-risk findings,
   attacker inference, defender next steps) + anti-hallucination rule
   ("do not claim a vulnerability unless the data supports it").
2. Wrapped it in pure functions so anything could reuse them:
   - `load_scan_data(path)` — JSON loader with clear `FileNotFoundError`
   - `build_nmap_analysis_prompt(scan_data)` — injects JSON into template
   - `generate_nmap_analysis(scan_data, preferred_model)` — Gemini call with a
     **model-fallback chain** (`_model_candidates()`: preferred → `GEMINI_MODEL`
     env → defaults), because single-model hardcoding proved fragile.
   - `analyze_scan_file(input, output, …)` — full file-to-Markdown flow.
3. Added `check_gemini_network()` — resolves `generativelanguage.googleapis.com`
   first so DNS failures produce an understandable message instead of a cryptic
   SDK stack trace.
4. Validated on the real localhost scan → `day9_nmap_llm_analysis.md`.

**Result:** end-to-end pipeline worked on the first target; identified ports
135/msrpc and 445/SMB with sensible remediation steps.

---

## 2. Day 10 — Refined Prompt (risk scoring + next steps, 3 test scans)

### What we built
Replaced the loose 4-point request with a **strict 5-section Markdown
template** the model must follow exactly:

| § | Section | Forces the model to produce |
|---|---------|------------------------------|
| 1 | Plain-English Summary | target, status, ports, system type |
| 2 | Risk Findings (ranked) | `Risk #N`, `Severity: <Level> (X/10)`, exact scan evidence |
| 3 | Attacker Perspective | defensive-only inferences + NSE audit scripts |
| 4 | Recommended Next Steps | split **Immediate (verification)** / **Hardening** |
| 5 | Confidence & Limitations | proven vs speculative + extra scans to run |

Built `test_day10_prompt_refinement.py` — resume-safe runner over **3 diverse
targets**: `127.0.0.1` (localhost), `scanme.nmap.org` (public practice host),
`172.16.2.1` (own gateway/router).

### Problems faced & how we tackled them

| # | Problem | Symptom | Root cause | Fix |
|---|---------|---------|-----------|-----|
| 1 | **IPv6 hang** | API calls froze for minutes on some hosts | Hostnames resolved to both A + AAAA records but machine had no IPv6 route; httpx waited on unreachable v6 | `force_ipv4_resolution()` — monkeypatch `socket.getaddrinfo` to force `AF_INET` for Google API hosts; calls went from hanging to seconds |
| 2 | **404 on model names** | Every request failed "model not found" | Docs-era names (`gemini-2.5-flash`, `gemini-2.0-flash`) were retired | Queried the live models endpoint; updated fallback chain to valid ones: `gemini-3.6-flash`, `gemini-flash-latest`, `gemini-3.5-flash`, `gemini-3.7-flash` |
| 3 | **Short client timeout** | Long, good generations killed mid-stream | Default HTTP timeout ≪ real generation time (2–5 min for full scans) | Explicit `HttpOptions(timeout=GEMINI_REQUEST_TIMEOUT_MS)` with `300_000` ms |
| 4 | **Transient 429/500/503** | Random failures between runs | Cloud rate limits / blips | Retry loop per model with **exponential backoff** (`5·2^attempt` s), retry only retryable statuses/timeouts |
| 5 | **Safety refusals** | Model refused to analyze our own router / scanme output | Benign security wording tripped automatic harm blocking; "owner of scanned systems" phrasing didn't cover public test hosts | Two-layer fix: (a) prompt explicitly frames DEFENSIVE education covering *"your own system OR authorized targets OR public test targets such as scanme.nmap.org"* and forbids exploit playbooks; (b) explicit `SafetySetting(BLOCK_NONE)` for harassment/hate/sexual/dangerous categories |

**Lesson:** reliability work (timeouts, retries, DNS, safety config) consumed
more time than the prompt itself — and it's what makes demos trustworthy.


---

## 3. Day 11 — Reusable Prompt-Engineering Module

### What we built
Generalized Day 10's single-purpose code into a small framework:

- `LLMProvider` enum (`GEMINI/OPENAI/CLAUDE/OLLAMA`) + `PromptMode` enum
  (`STANDARD/BEGINNER/REMEDIATION`)
- Two new templates: beginner-friendly (glossary + learning takeaways) and
  remediation plan (verify-now/fix/reference cards + OWASP/MITRE cross-check)
- `build_prompt(scan_data, mode=…)` dispatcher;
  `build_nmap_analysis_prompt()` kept as a **backwards-compatible alias**
- `ScanAnalysisResult` dataclass (provider, model, analysis, prompt, usage)
- `default_models_for_provider()` — env-overridable model lists
- Unified entry point `analyze_scan_data(provider=…, mode=…, …)`; Gemini logic
  refactored into `_call_gemini()` returning `(model, text, usage)`
- Offline unit-test suite `tests/test_prompt_engine.py`

### Problems faced & how we tackled them

| # | Problem | Symptom | Root cause | Fix |
|---|---------|---------|-----------|-----|
| 1 | **Shadowed function** | New alias ignored its `mode=` argument | The old Day 9 `build_nmap_analysis_prompt(scan_data)` still existed later in the file, overriding the new definition at import time | Deleted the legacy duplicate; added unit test asserting alias == standard prompt so the regression can't recur silently |
| 2 | **pytest not installed** | Test file couldn't run at all | pytest is Sneha's Week 3 deliverable; env didn't have it | Made the suite dual-mode: try-import pytest, else fall back to a tiny stub (`mark.parametrize` no-op decorator + `raises` context manager) so `python tests/test_prompt_engine.py` validates everything offline today, and real pytest picks it up unchanged in Week 3 |
| 3 | **monkeypatch dependency in tests** | One test required pytest fixtures | Used pytest's `monkeypatch` fixture | Rewrote to plain `os.environ` save/pop inside `try/finally` + temporarily neutralizing `load_dotenv` (otherwise `.env` reloads the deleted key!) |
| 4 | **Editing-tool whitespace mismatches** | Repeated failed replacements; stray `"""`; wrong indents | Long heredoc-style edits + CRLF quirks in some files | Switched strategy for stubborn files: small throwaway Python "fixer" scripts doing exact programmatic rewrites with `assert anchor in src` guards, verified by `py_compile` after every change |
| 5 | **Provider placeholders** | Risk of silent misbehavior when someone passes `provider="openai"` early | Not implemented yet by design | Explicit `NotImplementedError("planned for Day 12/13")` branches, locked in by unit tests |

**Procedure takeaway:** write the unit tests *with* the feature and run them
offline constantly — they caught bug #1, which would otherwise have shipped.

---

## 4. Day 12 — Ollama Support (local/private LLM)

### What we built
Local-model path so scans never need cloud or internet:

- `_ollama_model_candidates()` — candidate order: explicit arg → `OLLAMA_MODEL`
  env → **models actually installed on the server** (via `/api/tags`) →
  defaults (`llama3`, `llama3.1`, `gemma4`)
- `_call_ollama(prompt, …)` — `POST {OLLAMA_HOST}/api/generate`,
  `stream=false`, parses `response`, `prompt_eval_count`, `eval_count`,
  `total_duration`; a **404 (model not pulled) advances to next candidate**
  instead of failing
- `check_ollama_server()` health check with actionable message
  ("start `ollama serve`, pull a model"); `list_ollama_models()` helper
- Wired into the unified dispatch; `OLLAMA_HOST` env override; reused the
  already-present `requests` package — **zero new dependencies, zero API keys**

### Problems faced & how we tackled them

| # | Problem | Symptom | Root cause | Fix |
|---|---------|---------|-----------|-----|
| 1 | **No llama3 on the machine** | Sprint said "Llama 3", but `ollama list` showed only `gemma4:latest` (9.6 GB) | Only one model pulled locally | Don't hardcode llama3 — auto-detect installed models at runtime and walk the candidate list; any pulled model works |
| 2 | **First run timed out** | Wrapper hung ~5 min then failed; server looked idle | gemma4's **first-time weight load** (~9 GB from disk) took longer than the inherited 300 s (Gemini-style) timeout | Provider-aware timeouts: `timeout_ms=None` resolves **600 s for Ollama vs 300 s for Gemini** inside `analyze_scan_data`. After load, generation is fast (GPU) |
| 3 | **Looked idle but wasn't** | Low CPU/RAM made us think requests never arrived | Model was loading asynchronously; `ollama ps` stayed empty until finished | Diagnosed layer by layer: `netstat -ano | findstr 11434` (connections ESTABLISHED ✓), `ollama ps`, tail of `%LOCALAPPDATA%\Ollama\server.log` (showed `load_hparams … 9149 MiB`), then a raw minimal generate probe → `200 {"response":"OK"}` once loaded. Client code was fine — purely cold-start timing |
| 4 | **Test needed network** | New behavior couldn't be tested offline | Real HTTP to localhost | Mock-based tests: fake `requests` objects injected into the module to simulate unreachable server, happy-path parse, and 404→next-model fallback |
| 5 | **Stub broke exception handling** | `AttributeError: '_ConnErr' object has no attribute 'exceptions'` | Our fake replaced the whole `requests` module including the `exceptions` namespace used in `except` clauses | Fakes expose `exceptions = requests.exceptions` (the real classes) |

**Live validation:** smoke prompt 43.6 s → full localhost analysis, all 5
sections (`day12_analysis_localhost.md`). Privacy differentiator proven:
nothing left the machine.

---

## 5. Day 13 — LLM Switcher (`--llm` flag)

### What we built
Per team decision only **free** providers are active (gemini, ollama);
openai/claude are accepted by the CLI but refuse politely until wired:

- `resolve_provider(name)` — lower-cases input, maps to `LLMProvider`:
  - unknown name → "Unknown LLM provider 'x'. Valid providers: …"
  - `openai` / `claude` → "not wired up yet (paid API, planned for a later
    sprint day). Currently available FREE providers: gemini, ollama."
- `ACTIVE_PROVIDERS = {GEMINI, OLLAMA}` documents what's live today
- `--llm [gemini|ollama|openai|claude]` (case-insensitive, default gemini)
  added to the `analyze` command in **both** CLI entry points
  (`sentinelai/cli.py` and `commands/analyze.py`) identically
- `analyze_scan_file(provider=…)` now routes through the unified
  `analyze_scan_data()` — one code path for every provider; saved files get a
  `Provider: ollama | Model:` header

### Problems faced & how we tackled them

| # | Problem | Symptom | Root cause | Fix |
|---|---------|---------|-----------|-----|
| 1 | **Latent `--no-save` bug discovered** | Function returned `None` when saving disabled | Since Day 10, `return model, analysis` sat **inside** the `if output_file:` block | Moved the return outside the block. Classic case of an untested branch — now covered |
| 2 | **Duplicate command implementations** | Same `analyze` command exists in two files | Repo evolved with both `sentinelai/cli.py` and `commands/analyze.py` | Applied identical changes to both (duplication noted for Week 4 cleanup) so whichever entry point runs behaves the same |
| 3 | **Editor matching failures on cli.py** | Text-replace edits repeatedly "not found" despite visually identical content | CRLF/whitespace drift in that file | Programmatic fixer script with `assert anchor in src` guards + `py_compile` verification — same technique that rescued Day 11 |
| 4 | **Scope control** | Tempting to wire OpenAI/Claude "while we're here" | Paid APIs; sprint discipline + team decision to stay free | Kept them as first-class switcher choices that fail with guidance — honest UX, roadmap intact, zero spend |

**Live validation:** `--llm openai` refusal printed instantly with FREE
alternatives; full `--llm ollama` run generated `day13_analysis_ollama.md`
(all 5 sections) through the brand-new switcher path.

---

## 6. Cross-Cutting Lessons (Days 9–13)

1. **Fallback chains everywhere.** Models retire (404s), local models vary per
   machine — never trust a single hardcoded name; prefer env override →
   known-good list → runtime discovery.
2. **Timeouts must reflect reality.** LLM generations take minutes; cold model
   loads take minutes more. One shared timeout for two very different
   providers was wrong — make defaults provider-aware (`None` resolved
   internally per provider).
3. **Retry only what's transient** (429/500/503/timeouts) with exponential
   backoff; fail fast and loud on permanent errors with actionable messages.
4. **Defensive framing isn't optional** — it's what keeps cloud safety filters
   from refusing legitimate defensive analysis of your own machines.
5. **Offline-first testing.** Pure-function tests with tiny fakes caught a
   shadowing bug and enforced the provider contract before any network call.
   A pytest-stub keeps the suite runnable even before pytest lands in the venv.
6. **When text edits keep failing, go programmatic.** Small Python fixer
   scripts with assertions + immediate `py_compile` beat fighting whitespace.
7. **Diagnose in layers:** app log → connection table (`netstat`) → service
   status (`ollama ps`) → server log → raw one-line API probe. Each layer
   either clears or indicts the previous one.
8. **Resume-safe runners save demo day.** Skipping existing artifacts made
   iterating on long-running steps painless — and became the basis of the
   Day 14 team demo.

---

## 7. Commit Trail (evidence)

```
a4a1719 Day 8: Integrate Affan's NmapScanner into unified CLI …
5b55566 Day 9: Validate LLM prompt quality against real Nmap scan output …
8c5a252 Day 10: Refine LLM prompt - risk identification + next steps (3 test scans)
6819b00 Day 11: Complete prompt engineering module - reusable functions
1794cfe Day 12: Add Ollama support - local LLM analysis via local Ollama server
446f458 Day 13: Build LLM switcher - analyze --llm gemini|ollama|openai|claude flag
```

Detailed per-day reports: `WEEK_2_DAY_10_REPORT.md` → `WEEK_2_DAY_14_REPORT.md`.

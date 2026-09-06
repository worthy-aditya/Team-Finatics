# Week 4 — Day 24 Report: CLI Polish with Rich

**Date:** 2026-09-05 · **Owner:** Aditya · **Status:** ✅ COMPLETE (all suites green + live E2E)

**Sprint task (Day 24):** *Polish CLI output — add colors, progress indicators, clean status
messages → Terminal output looks professional using the Rich library.*

---

## 1. What was built

### `sentinelai/ui.py` — ONE shared terminal-UI layer (new, ~150 lines)
Both CLI entry points (`sentinelai.py` → `commands/` and `sentinelai/cli.py`) now render
through the same Rich console, so every command has identical professional output:

| API | Purpose |
|---|---|
| `info / success / warn / error` | Status lines: cyan `[*]`, green `[+]`, yellow/red `[!]` |
| `step(title)` | Section headers as full-width `rule()` |
| `kv(key, value)` | Aligned `Key: value` lines (network/report listings) |
| `spinner(text)` | Progress indicator (dots) wrapping long ops: nmap scans, LLM calls |
| `print_markdown(text)` | Rich-rendered Markdown for LLM analyses (headings/bullets) |
| `print_panel(text, title)` | Bordered panel for scan summaries |
| `clean(text)` | Escapes dynamic text so targets/IPs never trigger Rich markup |

Design guards (Weeks 1–3 lessons carried forward):
- **Non-TTY degradation:** Rich auto-plain-modes under pipes/tests/CI → captured output is
  guaranteed ANSI-free (asserted by `test_status_lines_are_ansi_free_when_captured`).
- **No-rich fallback:** a plain-text shim keeps every command working if `rich` is missing.
- **Machine paths untouched:** `--json` output stays plain `click.echo(json.dumps(...))`.

### Wiring (behavior-preserving swap, no parallel versions)
- `commands/scan.py`, `commands/analyze.py`, `commands/network.py`, `commands/report.py`
- `sentinelai/cli.py` (scan/analyze/version), `sentinelai/logs_command.py` (`logs`)
- `sentinelai/scanner.py`, `sentinelai/prompt_engine.py` (retry notices now styled)
- Day 20 approval flow reused as-is (`--confirm`/`--yes` on both `scan` commands)
- Deliberately **not** touched: `sentinelai/natural_cli.py` (self-consistent colorama REPL;
  follow-up issue), JSON document shapes, all LLM/pipeline logic.

## 2. Real bugs found & fixed during validation (pipe-testing paid off)

1. **`logs --json` stdout was not JSON-pure** *(pre-existing since Day 18/22)*: the human
   `[*] Read N events...` line printed to stdout before the JSON document, breaking
   `sentinelai logs --json | jq`. Fix: human status lines now gated behind `not output_json`
   (file writing still happens). Verified byte-clean on both CLIs.
2. **`scan --output-json` could be polluted by scanner internals** *(pre-existing)*: added
   `NmapScanner(target, quiet=False)`; in `--output-json` mode the scanner suppresses stdout
   status/error lines (failures still reach the logger + `scan_errors` → error JSON).
3. **Group-callback banner trap:** an initial version printed a banner in `sentinelai.py`'s
   group callback — which runs before *every* subcommand and corrupted piped JSON. Removed;
   branding lives in help text instead.

## 3. Validation

| Check | Result |
|---|---|
| `tests/test_ui.py` (new: API surface, ANSI-free capture, spinner contract, md/panel, JSON purity) | **6/6 PASS** |
| `test_event_bridge` / `test_routing` / `test_log_parser` / `test_cli_sync` | **5/5, 5/5, 8/8, 3/3 PASS** |
| `test_prompt_engine` | **PASS** |
| Live `logs --sample --analyze --llm ollama` (gemma4) via new UI | **RC=0**, 5/5 sections, status+spinner path exercised |
| `logs --sample --json` piped to `json.loads` (root + package CLIs) | **Pure JSON ✓** (byte-level, no ANSI) |
| `network`, `--help` both CLIs | Clean rendered output ✓ |
| `py_compile` on all 10 touched modules | OK |

## 4. Files

**New:** `sentinelai/ui.py`, `tests/test_ui.py`
**Modified:** `sentinelai.py`, `sentinelai/cli.py`, `sentinelai/logs_command.py`,
`sentinelai/scanner.py`, `sentinelai/prompt_engine.py`, `commands/{scan,analyze,network,report}.py`
(`rich==15.0.0` already pinned in `requirements.txt` — no dependency change)

## 5. Next (Day 25)

One-command E2E test (scan → analyze) + demo rehearsal for the Week 4 review.

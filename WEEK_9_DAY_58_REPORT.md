# WEEK_9_DAY_58_REPORT.md

## Day 58 - `health` Command Group (Profiles + Status)

### Week
Week 9. Builds on Day 57 (health profiles) and the Week 8 health primitives.

### Task
Give provider health a first-class CLI home. Day 57 added saveable/loadable
health profiles, but they could only be managed from Python, and the
dashboard/alerts were only reachable through `analyze` short-circuit flags. Day
58 adds a `health` command group (registered on BOTH CLI entry points) that
exposes profile management and a combined status view as subcommands.

### Delivered
1. **Added `sentinelai/health_command.py`** (new module, fully offline):
   - `build_health_command()` factory (mirrors `build_logs_command`) returns a
     Click group `health` with subcommands:
     - `health profiles` — list saved profiles.
     - `health save NAME (--scores JSON | --scores-file PATH)` — save a profile.
     - `health show NAME` — print a profile's scores.
     - `health delete NAME` — delete a profile (missing = warning, not fatal).
     - `health status [--profile NAME] [--record]` — render the dashboard (with
       optional per-provider trends when `--record`) followed by the alerts
       report, all in one view.
   - Reuses the existing primitives: `dashboard.build_dashboard`,
     `health_alerts.detect_alerts` / `build_alerts_report`,
     `health_history.record_snapshot` / `load_history` / `summarize_trends`, and
     the Day 57 `health_profiles` CRUD functions. No analysis logic re-implemented.

2. **Registered `health` on BOTH CLI entry points**:
   - `sentinelai/cli.py` (the `main` group) and the root `sentinelai.py` (the
     `cli` group) both call `main/cli.add_command(build_health_command())`, so
     `sentinelai health ...` works identically from either entry point.

3. **Added `tests/test_day58_health_command.py`**:
   - 12 tests via Click's `CliRunner`, run inside a throwaway working directory
     so the real `provider_profiles/` is never touched: empty profiles list,
     save (inline JSON and via file) then list, show (present + missing),
     delete (present + missing/not-fatal), save-requires-scores usage error,
     `status` rendering the dashboard, `status --profile` (ollama 55 -> LOW),
     `status --profile` unknown -> error, and registration of the `health` group
     on both entry points (with subcommand set check). All offline.

### Validation
- Day 58 tests: **12 passed** (direct run and via pytest).
- CLI parity (`test_cli_sync.py`): **6 passed** (analyze unchanged; `health`
  registered on both entry points, verified in the Day 58 registration test).
- Full test suite: **290 passed** (was 278, +12 Day 58; offline; no LLM or
  network calls).
- Verified end-to-end: `sentinelai health --help` lists all five subcommands;
  `health save --scores-file` + `health show` + `health profiles` round-trip a
  `baseline` profile; `health status` renders the dashboard + alerts; the root
  `sentinelai.py --help` shows the `health` command. Test artifacts cleaned up.
- No new external dependencies.

### External Dependencies
None. The command group is pure Click + stdlib and reuses existing offline
modules; no new packages required.

### Outcome
Day 58 makes the Week 8/9 provider-health subsystem operable from the CLI.
Operators can now manage reproducible health profiles (`health save/show/
profiles/delete`) and get a one-shot operational view (`health status`) that
combines the dashboard and alerts - all offline. This completes the profile
lifecycle started on Day 57 (create -> use -> inspect -> remove) at the CLI
layer and sets up further operational tooling for the rest of Week 9.

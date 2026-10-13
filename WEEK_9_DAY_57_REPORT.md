# WEEK_9_DAY_57_REPORT.md

## Day 57 - Provider Health Profiles

### Week
Week 9 (opens the week). Builds directly on the Week 8 provider-health engine.

### Task
Make provider health **reproducible**. Week 8's health primitives (dashboard,
history, alerts, health-gated routing) all consumed ad-hoc provider scores
supplied via a `--provider-scores` JSON file. Day 57 adds saveable/loadable
**named health profiles** and a `--profile` option, so `sentinelai analyze` can
run against a known-good, degraded, or demo health state without touching a live
provider - useful for CI/regression baselines and demos.

### Delivered
1. **Added `sentinelai/health_profiles.py`** (new module, fully offline):
   - `save_profile()` — persist a named `{provider: score}` set as a JSON
     document `{name, saved_at, scores}` under `provider_profiles/`; overwrites
     an existing profile of the same name.
   - `load_profile()` — return the `{provider: score}` map for a profile;
     raises `FileNotFoundError` when missing and `ValueError` when corrupt.
   - `list_profiles()` — sorted list of saved profile names.
   - `delete_profile()` — remove a profile; returns whether a file was removed.
   - `profile_exists()` and `profile_path()` helpers.
   - **Name validation** (`_validate_name`): names must be simple identifiers
     (`[A-Za-z0-9][A-Za-z0-9_-]*`), so a name can never escape the profiles
     directory (no path separators / traversal) or collide with the `.json`
     suffix. Constant `DEFAULT_PROFILES_DIR = "provider_profiles"`.

2. **Wired `--profile` into both `analyze` entry points**:
   - Added the option to `commands/analyze.py` and `sentinelai/cli.py` (kept in
     sync for `test_cli_sync.py`). When `--provider-scores` is not supplied,
     `--profile NAME` loads the named profile as the provider scores, feeding the
     existing dashboard / alerts / health-gated routing pipeline. A missing or
     corrupt profile produces a clean error and aborts (no traceback).

3. **Added `tests/test_day57_health_profiles.py`**:
   - 16 unit tests covering: save/load round-trip, stored JSON document shape,
     sorted listing, deletion (+ idempotency), existence checks, missing/corrupt
     load errors, overwrite semantics, invalid-name rejection (traversal,
     separators, spaces, leading dot, `.json` suffix), valid dash/underscore
     names, empty/non-numeric score rejection, path-traversal blocked at the
     path layer, the default-dir constant, and `--profile` parity across both
     CLIs. All offline, pure functions.

### Validation
- Day 57 tests: **16 passed** (direct run and via pytest).
- CLI parity (`test_cli_sync.py`): **6 passed** — `--profile` present on both
  `analyze` entry points.
- Full test suite: **278 passed** (was 262, +16 Day 57; offline; no LLM or
  network calls).
- Verified end-to-end: saved a `degraded` profile
  (`gemini 92 / ollama 55 / deepseek 80`), then `analyze --dashboard --profile
  degraded` rendered the dashboard with ollama correctly flagged `LOW`; a
  missing profile produced a clean `Could not load provider health profile`
  error.
- No new external dependencies.

### External Dependencies
None. The module is pure Python (stdlib `json`, `re`, `datetime`, `pathlib`);
no new packages required.

### Outcome
Week 9 opens by making the Week 8 health engine **operable and reproducible**.
Provider health states can now be saved under names (e.g. a `baseline` for CI,
a `degraded` state to exercise alert/quarantine paths, a `demo` state for
presentations), listed, loaded via `--profile`, and deleted - all offline. This
sets up the operational tooling that the rest of Week 9 will build on.

# WEEK_8_DAY_55_REPORT.md

## Day 55 - Provider Health Alerting

### Task
Turn recorded provider health history (Day 54) into **actionable alerts** so an
operator is told when a provider needs attention instead of having to read the
dashboard/trends manually. Raise an alert when a provider is either **critical**
(latest score below the healthy threshold) or **warning** (still healthy but
actively *degrading*, i.e. trending toward the threshold).

### Delivered
1. **Added `sentinelai/health_alerts.py`** (new module, fully offline):
   - `HealthAlert` dataclass — `provider`, `severity` (`critical`|`warning`),
     `reason`, `score`, `trend`, plus `to_dict()`.
   - `detect_alerts()` — scans recorded history and returns actionable alerts:
     * `critical` when a provider's latest score is below the healthy threshold
       (70.0), or
     * `warning` when a provider is healthy but its trend is `degrading`.
     Alerts are sorted most-severe first (critical before warning), then
     alphabetically by provider. Empty/no-alert history yields `[]`.
   - `summarize_alerts()` — returns `{"critical": n, "warning": n}` counts.
   - `build_alerts_report()` — renders a human-readable alerts table with a
     severity header and per-alert reason.
   - Constants: `HEALTHY_THRESHOLD = 70.0` (kept in sync with
     `routing.provider_is_healthy`), `SEVERITY_ORDER`.

2. **Wired `--alerts` into both `analyze` entry points**:
   - Added the flag to `commands/analyze.py` and `sentinelai/cli.py` (kept in
     sync for `test_cli_sync.py`). `--alerts` short-circuits analysis and prints
     the alerts report derived from the recorded history file. When combined
     with `--health-history`, it records the current scores as a snapshot first
     so alerts reflect the latest data.

3. **Added `tests/test_day55_health_alerts.py`**:
   - 13 unit tests covering: empty history, critical (below threshold),
     warning (degrading while healthy), no-alert (healthy + stable),
     critical-priority-over-trend, severity sorting, alert summary counts
     (empty and populated), the alerts report (empty and rendered), the healthy
     threshold constant, `HealthAlert.to_dict()`, and `--alerts` parity across
     both CLIs. All offline, pure functions.

### Validation
- Day 55 tests: **13 passed** (direct run and via pytest).
- Full test suite: **250 passed** (was 237, +13 Day 55; offline; no LLM or
  network calls).
- CLI parity (`test_cli_sync.py`): **6 passed** — `--alerts` present on both
  `analyze` entry points.
- Verified end-to-end: a below-threshold provider (ollama 45.0) reported as
  `CRITICAL`; a provider that then dropped 90 -> 80 additionally reported as
  `WARNING` (degrading); the report sorted critical before warning.
- No new external dependencies.

### External Dependencies
None. The alerts module is pure Python and only depends on
`sentinelai.health_history` (stdlib-backed); no new packages required.

### Outcome
Day 55 completes the observability-to-action loop. Days 50-54 gave the system
fallback (resilience), scoring (intelligence), routing (automation), a registry
+ dashboard (management), and history + trends (observability). Day 55 adds
**alerting**: the system now proactively flags providers that are below the
healthy threshold (`critical`) or actively degrading (`warning`) via
`sentinelai analyze --alerts`, so operators are told when to intervene.

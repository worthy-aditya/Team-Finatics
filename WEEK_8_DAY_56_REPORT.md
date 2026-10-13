# WEEK_8_DAY_56_REPORT.md

## Day 56 - Health-Gated Provider Selection

### Task
Close the automation loop between detection and routing. Day 55 detects
providers below the healthy threshold as "critical", and Day 52's
`recommend_provider()` picks the highest-scoring eligible provider — but it will
still choose a provider that is *below* the healthy threshold if that happens to
be the best of a weak field. Day 56 makes routing **quarantine** providers whose
current score is below the healthy threshold, so a sick provider is skipped
whenever a healthy alternative exists.

### Delivered
1. **Added `sentinelai/health_router.py`** (new module, fully offline):
   - `quarantine_by_score()` — returns the sorted list of providers whose score
     is below the healthy threshold (default 70.0, reused from
     `health_alerts.HEALTHY_THRESHOLD`).
   - `health_gate()` — summarises providers into `healthy` / `quarantined` /
     `all_unhealthy` plus the threshold used.
   - `ProviderChoice` dataclass — `provider`, `quarantined`, `all_unhealthy`,
     a `fallback_used` property, and `to_dict()`.
   - `recommend_healthy_provider()` — wraps the Day 52 `recommend_provider()`
     logic but first removes below-threshold providers from the candidate pool.
     Honours the routing/sensitivity rules. When *every* provider is unhealthy
     it falls back to the least-bad of the full pool and sets `all_unhealthy`
     so callers can warn. Raises `ValueError` for an empty score set.

2. **Wired health-gated selection into both `analyze` entry points**:
   - Updated `commands/analyze.py` and `sentinelai/cli.py` so the
     `--provider-scores` path now uses `recommend_healthy_provider()` instead of
     `recommend_provider()`. When providers are quarantined it reports them; when
     none are healthy it warns that it is using the least-bad option.
   - Kept both entry points in sync (locked by `tests/test_cli_sync.py`).
   - Side benefit: fixed a latent `NameError` — `sentinelai/cli.py` previously
     called `recommend_provider()` without importing it; it now imports and uses
     `recommend_healthy_provider()`. Removed the now-unused `recommend_provider`
     import from `commands/analyze.py`.

3. **Added `tests/test_day56_health_router.py`**:
   - 12 unit tests covering: quarantine detection (boundary at threshold, custom
     threshold, all-healthy), the health gate partitions + `all_unhealthy`,
     avoiding a quarantined higher-scoring provider, picking the best healthy
     provider, the all-unhealthy fallback, routing-policy compliance, empty
     scores raising, `ProviderChoice.to_dict()`, and the re-exported threshold.
     All offline, pure functions.

### Validation
- Day 56 tests: **12 passed** (direct run and via pytest).
- Health-suite regression (Days 52-56 + CLI parity): **64 passed**.
- Full test suite: **262 passed** (was 250, +12 Day 56; offline; no LLM or
  network calls).
- CLI parity (`test_cli_sync.py`): **6 passed**.
- Verified: a provider scoring 69.0 (below the 70 threshold) is quarantined and
  a healthy 75.0 provider is selected instead.
- No new external dependencies.

### External Dependencies
None. The module only depends on `sentinelai.routing` and
`sentinelai.health_alerts` (both pure Python); no new packages required.

### Outcome
Day 56 completes the Week 8 health automation loop: providers are scored
(Day 51), routed (Day 52), monitored over time (Day 54), alerted on when
unhealthy (Day 55), and now **automatically excluded from selection when below
the healthy threshold** (Day 56). Routing is now resilient not just to hard
failures (Day 50 fallback) but also to *degraded* providers, choosing a healthy
alternative whenever one exists.

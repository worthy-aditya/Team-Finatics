# Week 6 - Day 41 Report (Feature Sprint)

**Date:** 2026-10-06  
**Owner:** Team Finatics / SentinelAI active-testing track  
**Plan task:** Make the live active-scan path prove the local ZAP daemon is reachable before it begins a scan, and add a smoke harness for the Juice Shop + ZAP validation path.  
**Status:** COMPLETE - the authorized scan path now performs a live readiness check before executing a real active request.

---

## 1. Why This Task Was Needed

Day 40 closed the execution gap: the `--active` flow finally invoked the authorized ZAP check after the consent and domain gates passed. The remaining gap was operational readiness. If the local ZAP daemon was down or unreachable, the system would still fail late and ambiguously, which is not a good fit for a fail-closed security workflow.

The required behavior for the live environment is straightforward:

- the scan must only start after the authorization gates pass;
- the ZAP daemon must be reachable before the scan begins; and
- a broken local environment must fail with a specific, traceable error, not a vague generic failure.

This is the Day 41 hardening step for the real Juice Shop validation path.

---

## 2. What Was Completed

| File | Deliverable |
|---|---|
| `sentinelai/active_gate.py` | `run_authorized_active_checks()` now calls `ZAPClient.version()` before starting the active scan |
| `tests/test_day41_live_zap_harness.py` | Smoke regression for the live ZAP reachability preflight |
| `WEEK_6_DAY_41_REPORT.md` | Day 41 proof record |
| `WEEK_6_SUMMARY.md` | Sprint summary updated with Day 41 completion |

The new behavior is intentionally simple and robust:

```python
zap_client = client or ZAPClient(...)
zap_client.version()
```

This ensures the environment can prove the daemon is alive before the actual active-scan request is sent.

---

## 3. Methods Used

### 3.1 ZAP reachability preflight

Before `ZAPActiveCheck.run()` begins the active scan, the helper verifies the local daemon is reachable by calling `core/view/version`. This turns a deployment issue into a clear and actionable error rather than a hidden runtime break.

### 3.2 Real-environment smoke harness

The Day 41 smoke test checks that the helper performs the reachability check before delegating to the ZAP active-check orchestration. This is the same live path that the CLI uses in production, so it acts as a guardrail against future regressions in the real environment.

### 3.3 Fail-closed behavior

The helper still enforces all of the original active-scan constraints:

- consent is required;
- domain verification is required;
- `--yes` is still rejected;
- the target must be URL-shaped for ZAP active requests; and
- the actual scan still runs only with `active_authorized=True`.

Day 41 strengthens the environment readiness check without weakening the security boundaries.

---

## 4. Validation

Focused validation was run:

```powershell
.\venv\Scripts\python.exe -m pytest tests/test_day41_live_zap_harness.py tests/test_day40_active_scan_integration.py tests/test_day38_checks.py tests/test_day39_risk_weighting.py -q
```

Result:

```text
16 passed, 1 warning
```

Full repository validation was also run:

```powershell
.\venv\Scripts\python.exe -m pytest -q
```

Result:

```text
182 passed, 1 warning in 45.49s
```

The warning remains the existing Google GenAI deprecation warning and is unrelated to the Day 41 fix.

---

## 5. Scope and Limits

- This day validates the live ZAP readiness preflight rather than claiming a fully populated Juice Shop scan result.
- The actual app-level findings still require a reachable local ZAP daemon and the target app to be up.
- The code continues to enforce explicit authorization rather than silently ignoring the environment state.

---

## 6. Next Task

The repository is now prepared for the true Juice Shop + ZAP validation run: the active path proves the daemon is reachable before launch, and the CLI remains fail-closed from consent through execution. The next operational move is to run the same helper against a live local Juice Shop instance with ZAP enabled and inspect the normalized findings output.

**Commit-ready files:** `sentinelai/active_gate.py`, `tests/test_day41_live_zap_harness.py`, `WEEK_6_DAY_41_REPORT.md`, `WEEK_6_SUMMARY.md`

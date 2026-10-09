# Week 6 - Day 40 Report (Feature Sprint)

**Date:** 2026-10-01  
**Owner:** Team Finatics / SentinelAI active-testing track  
**Plan task:** Finish the real `--active` execution path by running the authorized ZAP check after consent + domain verification, then validate the integration in the repo regression suite.  
**Status:** COMPLETE - the active gate now triggers the ZAP plugin path, the CLI remains fail-closed, and the full regression suite passes.

---

## 1. Why This Task Was Needed

The project already had the safer pieces of the design:

- consent gate;
- domain verification; and
- reusable ZAP check contract + ranking logic.

What was still missing was the final execution step. After a successful auth flow, the CLI stopped at the Nmap scan path and never instantiated the actual ZAP check. That left the architecture in a valid but unused state: all the active-scan safety boundaries existed, but the real active check was never invoked in the live command path.

This gap mattered because an operator could not tell whether `--active` truly triggered the live ZAP path after passing authorization. The underlying issue was not in the consent/DNS gate itself; it was that no single helper connected authorization to the authorized ZAP executor.

---

## 2. What Was Completed

| File | Deliverable |
|---|---|
| `sentinelai/active_gate.py` | Shared `run_authorized_active_checks()` helper that executes the ZAP active check only after authorization passes |
| `commands/scan.py` | Root CLI `scan --active` path now calls the real ZAP check before continuing with the host scan |
| `sentinelai/cli.py` | Package CLI `scan --active` path is parity-locked to the root CLI and invokes the same live active-check helper |
| `tests/test_day40_active_scan_integration.py` | Regression test covering the missing pipeline: auth gate → ZAP orchestrator execution |
| `WEEK_6_DAY_40_REPORT.md` | Day 40 implementation and verification record |

The Day 40 fix enforces the intended sequence:

1. user enables `--active`;
2. consent gate runs;
3. domain verification runs;
4. if authorization succeeds, the CLI executes `ZAPActiveCheck` through `run_all_checks(..., active_authorized=True)`;
5. then the existing Nmap path continues as before.

---

## 3. Methods Used

### 3.1 Shared execution helper

The new helper in `sentinelai/active_gate.py` accepts the user target, upcasts a bare hostname to a URL (when needed), and calls the shared ZAP active box through the orchestrator:

```python
run_all_checks(target, [ZAPActiveCheck(zap_client)], active_authorized=True)
```

This keeps the authorization boundary explicit and separate from the active traffic execution. The helper does not broaden consent or domain-check rules; it only invokes the authorized check after the gate has already succeeded.

### 3.2 CLI wiring

Both `commands/scan.py` and `sentinelai/cli.py` now call the helper immediately after the successful `authorize_active_testing()` result. If the target is not URL-shaped, the helper ensures it is converted to a URL. If the ZAP daemon is unreachable, the CLI raises a clear `ClickException` so the operator knows the active-scan environment is not ready.

### 3.3 Safety boundary

The system remains fail-closed:

- `--yes` is still rejected for active testing;
- consent must still be typed exactly;
- domain verification still must pass; and
- ZAP execution still requires the explicit authorization flag.

The Day 40 addition simply makes the already-defined active-check contract actually run.

---

## 4. Validation

Focused validation was run first:

```powershell
.\venv\Scripts\python.exe -m pytest tests/test_day40_active_scan_integration.py tests/test_cli_sync.py tests/test_day38_checks.py tests/test_day39_risk_weighting.py -q
```

Result:

```text
15 passed, 1 warning
```

Full regression validation:

```powershell
.\venv\Scripts\python.exe -m pytest -q
```

Result:

```text
182 passed, 1 warning in 45.49s
```

The warning is the existing Google GenAI deprecation warning from the dependency stack; no new functional failures were introduced.

---

## 5. Scope and Limitations

- The Day 40 work completes the active-check execution path, not a new exploit engine.
- SentinelAI still delegates real attack traffic generation to OWASP ZAP, per the project’s architecture.
- A live active scan still depends on a reachable ZAP daemon and a properly authorized target.
- This fix does not bypass the existing authorization gate; it makes the authorized path real and measurable.

---

## 6. Next Task

The repository is now aligned with the sprint design: the CLI runs the active ZAP check only after the consent and domain gates pass, and the findings are ranked by confirmed posture and risk score. The next project step is practical validation against a live local Juice Shop + ZAP stack if the environment is available.

**Commit-ready files:** `sentinelai/active_gate.py`, `sentinelai/cli.py`, `commands/scan.py`, `tests/test_day40_active_scan_integration.py`, `WEEK_6_DAY_40_REPORT.md`

# Week 6 - Day 38 Report (Feature Sprint)

**Date:** 2026-10-01  
**Owner:** Team Finatics / SentinelAI active-testing track  
**Plan task:** Wire the ZAP active scan into the plugin/orchestrator architecture as a proper active check; refine ZAP analysis around OWASP/MITRE evidence.  
**Status:** COMPLETE for the Day 38 architecture slice - offline contract and safety tests pass. A live ZAP daemon and Juice Shop scan remain Day 40 validation work.

---

## 1. Why This Task Was Needed

Days 31-37 established the authorization boundary and the ZAP findings-analysis path, but SentinelAI still had no execution abstraction for active checks. The existing `--active` flow verified consent and domain control, then continued into the Nmap stage; it did not yet have a reusable way to invoke ZAP, collect alerts, or combine ZAP with future passive checks.

Without a shared check contract, each future scanner would need its own result shape and orchestration logic. That would make it easy to bypass authorization, lose whether a finding was active or passive, and create another parallel pipeline outside the existing ZAP prompt/report path.

Day 38 therefore establishes the smallest common execution layer:

- independent vulnerability-check boxes;
- explicit passive versus active classification;
- one normalized `Finding` object;
- an orchestrator that isolates failures between checks; and
- a ZAP adapter that cannot run active traffic without an explicit authorization flag.

---

## 2. What Was Completed

| File | Deliverable |
|---|---|
| `sentinelai/checks/base.py` | `CheckType`, `Finding`, and abstract `VulnerabilityCheck` contracts |
| `sentinelai/checks/orchestrator.py` | `run_all_checks()` for independent check execution and error collection |
| `sentinelai/checks/zap.py` | ZAP JSON API client, active-scan polling, alert normalization, and authorization guard |
| `sentinelai/checks/__init__.py` | Public package exports |
| `tests/test_day38_checks.py` | Focused contract, safety, polling, normalization, and orchestration tests |
| `sentinelai/prompt_engine.py` | ZAP prompt now requires evidence-based OWASP/MITRE mapping language |

The new adapter produces the same core alert fields already accepted by
`build_zap_prompt()` and `analyze_zap_findings_data()`, so the Day 36 LLM path
can consume normalized results without a second analysis pipeline.

---

## 3. Methods Used

### 3.1 Contract-first plugin design

`VulnerabilityCheck` is an abstract base class with a single `run()` method. Each implementation declares a name and a `CheckType`. The method receives the target and an `active_authorized` flag, keeping the authorization decision visible at the execution boundary.

`CheckType.PASSIVE` represents observation-only checks. `CheckType.ACTIVE` represents checks that send test traffic. The `Finding` dataclass carries source, risk, confidence, evidence, URL, method, parameter, plugin/CWE identifiers, remediation fields, and optional OWASP/MITRE mappings.

### 3.2 Fail-closed authorization

`ZAPActiveCheck.run()` refuses to call the ZAP client unless `active_authorized=True`. It also rejects bare hostnames and requires an explicit `http://` or `https://` URL because ZAP active scanning targets web origins, not Nmap host strings.

The check does not create or infer authorization. The existing consent and domain-verification flow remains responsible for producing authorization; the caller must pass that successful result explicitly.

### 3.3 ZAP API integration

`ZAPClient` uses the existing `requests` dependency and ZAP's JSON API:

1. `core/view/version` confirms that the daemon is reachable.
2. `ascan/action/scan` starts the active scan.
3. `ascan/view/status` is polled until progress reaches 100 percent.
4. `core/view/alerts` retrieves the resulting alerts.

The client supports a configurable base URL, API key, request timeout, polling interval, and maximum scan duration. Network failures, invalid JSON, missing scan IDs, API failure responses, and timeouts become actionable `ZAPError` exceptions.

### 3.4 Schema normalization

ZAP commonly returns camelCase fields such as `pluginId` and `cweid`, while the SentinelAI fixture uses `plugin_id` and `cwe_id`. `normalize_zap_alert()` accepts both forms and returns a shared `Finding` object. `Finding.to_dict()` converts the internal `parameter` field to the existing external `param` field and adds:

- `check_type: "active"`;
- `confirmed: true` for active findings; and
- the original evidence, attack, tags, solution, and reference fields.

This preserves the Day 35/36 ZAP schema while adding provenance needed for Day 39 risk weighting.

### 3.5 Failure isolation

`run_all_checks()` runs every check independently. A daemon failure in the ZAP box is recorded under `errors` and does not remove findings returned by other boxes. The result includes the target, executed check names, normalized findings, errors, and total count.

---

## 4. Detailed Behavior

### Unauthorized execution

```python
check.run("http://juice-shop.local")
```

Fails before making any HTTP request and reports that `active_authorized=True` is required.

### Authorized execution

```python
result = run_all_checks(
    "http://juice-shop.local",
    [ZAPActiveCheck(zap_client)],
    active_authorized=True,
)
```

The ZAP box starts the scan, waits for completion, normalizes each alert, and returns findings with `check_type="active"` and `confirmed=true`.

### Example normalized finding

```json
{
  "name": "SQL Injection",
  "risk": "High",
  "confidence": "Medium",
  "check_type": "active",
  "confirmed": true,
  "source": "zap-active-scan",
  "plugin_id": 40018,
  "cwe_id": 89,
  "url": "http://juice-shop.local/rest/products/search?q=1",
  "method": "GET",
  "param": "q"
}
```

“Confirmed” here means that ZAP actively sent a request and observed the alert condition. It does not claim that business impact or exploitability has been independently verified; the existing ZAP prompt keeps that distinction explicit.

---

## 5. Validation

Focused validation was run without a ZAP daemon or network target:

```powershell
.\venv\Scripts\python.exe -m pytest tests/test_day38_checks.py tests/test_zap_prompt.py -q
```

Result:

```text
18 passed, 1 warning
```

The tests cover:

1. no API call when active authorization is absent;
2. complete URL validation;
3. camelCase and snake_case ZAP field normalization;
4. active-scan start, polling, completion, and alert retrieval;
5. active finding provenance and confirmation status; and
6. independent-check failure isolation.

A live ZAP/Juice Shop run was intentionally not claimed as part of this validation. That requires the ZAP daemon and local Juice Shop environment and belongs to the Day 40 integration check.

---

## 6. Security and Scope Notes

- The project still delegates active request generation to OWASP ZAP; SentinelAI does not implement exploit payloads.
- The adapter does not weaken the existing consent or domain-verification gates.
- The API key, when configured, is passed to ZAP as a request parameter and is not written to findings.
- The current `--active` CLI command is not yet wired to instantiate `ZAPActiveCheck`; that integration is the next wiring step after the contract is reviewed.
- Report appendices, ZAP-to-OWASP/MITRE lookup tables, risk weighting, and real Juice Shop validation remain later Day 38-42 work.

---

## 7. Next Task

The next implementation step is to wire the shared authorization result and target URL into the CLI/orchestrator, then add a real local ZAP/Juice Shop integration harness. After that, Day 39 can use `check_type` and `confirmed` to score active findings above passive findings.

**Commit-ready files:** `sentinelai/checks/`, `tests/test_day38_checks.py`, `sentinelai/prompt_engine.py`, `WEEK_6_DAY_38_REPORT.md`

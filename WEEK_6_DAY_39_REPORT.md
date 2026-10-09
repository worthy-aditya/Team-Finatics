# Week 6 - Day 39 Report (Feature Sprint)

**Date:** 2026-10-01  
**Owner:** Team Finatics / SentinelAI active-testing track  
**Plan task:** Add risk-weighting logic so confirmed active findings score higher than potential passive findings.  
**Status:** COMPLETE - deterministic scoring, confirmed-first ranking, focused tests, and full regression validation.

---

## 1. Why This Task Was Needed

Before Day 39, SentinelAI could label a finding as active or passive through
`CheckType`, but that provenance did not affect prioritization. A potential
finding inferred from passive observation could therefore appear equal to a
finding produced by an authorized active check that sent a request and
observed a response condition.

That distinction matters to a defender. Active evidence deserves stronger
investigative priority, while passive observations should remain clearly
qualified as potential. The system must make this distinction programmatically
rather than relying on an LLM to infer it from prose.

The implementation also needed to avoid a common mistake: changing a scanner's
reported severity just because the source was active. A High ZAP alert remains
High; confirmation changes the priority score and posture, not the underlying
label or a claim of business impact.

---

## 2. What Was Completed

| File | Deliverable |
|---|---|
| `sentinelai/checks/base.py` | Bounded risk score and confirmed/potential posture on `Finding` |
| `sentinelai/checks/orchestrator.py` | Deterministic confirmed-first `rank_findings()` ordering |
| `sentinelai/checks/__init__.py` | Public export for `rank_findings()` |
| `tests/test_day39_risk_weighting.py` | Focused tests for score, serialization, bounds, and ordering |
| `WEEK_6_DAY_39_REPORT.md` | Day 39 implementation and verification record |

Day 38 output now carries two additional fields:

```json
{
  "risk_posture": "confirmed",
  "risk_score": 91
}
```

Passive findings receive `risk_posture: "potential"`; active findings receive
`risk_posture: "confirmed"`.

---

## 3. Methods Used

### 3.1 Deterministic severity baseline

The score starts from a fixed severity table:

| Reported risk | Baseline |
|---|---:|
| Critical | 80 |
| High | 65 |
| Medium | 45 |
| Low | 25 |
| Informational / Info | 10 |

Unknown risk values use the conservative informational baseline rather than
raising an exception or inventing a severity.

### 3.2 Confidence adjustment

The scanner's confidence field adds a small evidence-quality adjustment:

| Confidence | Bonus |
|---|---:|
| High | 10 |
| Medium | 6 |
| Low | 2 |
| Unknown | 0 |

This keeps confidence meaningful without allowing confidence alone to outrank
the active/passive posture.

### 3.3 Confirmation weighting

Active findings receive a confirmation bonus of 20 points. Passive findings
receive no confirmation bonus.

The formula is:

```text
risk_score = min(100, severity_baseline + confidence_bonus + confirmation_bonus)
```

This means an active High/Medium finding scores 91 while an equivalent passive
High/Medium finding scores 71. The score is bounded to 100 for stable report
and API output.

### 3.4 Confirmed-first ranking

`rank_findings()` sorts by:

1. confirmed active posture;
2. descending numeric risk score; and
3. finding name as a stable alphabetical tie-breaker.

The first key deliberately makes confirmation visible in the queue. A finding
is not silently reclassified as confirmed because of its name, risk level, or
LLM wording; only `CheckType.ACTIVE` creates confirmed posture.

### 3.5 Serialization

`Finding.to_dict()` now preserves the existing `risk` and `confidence` fields
and adds:

- `confirmed`: boolean compatibility field;
- `risk_posture`: `confirmed` or `potential`; and
- `risk_score`: integer from 0 to 100.

This keeps the output usable by the Day 36 ZAP prompt while making the data
available to future reports, CLI summaries, and Day 40 real-scan validation.

---

## 4. Detailed Behavior

### Equivalent active and passive findings

```python
passive.risk_score  # 71 for High / Medium
active.risk_score   # 91 for High / Medium
```

Both findings still report `risk == "High"`. Only the evidence posture and
priority score differ.

### Orchestrator output

The existing `run_all_checks()` path now ranks findings before serializing
its result. This means every consumer receives a consistent order, whether
findings came from ZAP or a future passive check box.

### Safety boundary

The score does not grant authorization, trigger a scan, or prove real-world
exploitability. Authorization remains controlled by the Day 31-34 consent and
domain-verification flow. The score only communicates how strongly the result
should be prioritized after a check has run.

---

## 5. Validation

Focused validation:

```powershell
.\venv\Scripts\python.exe -m pytest tests/test_day39_risk_weighting.py tests/test_day38_checks.py -q
```

Result:

```text
8 passed
```

Full regression validation:

```powershell
.\venv\Scripts\python.exe -m pytest -q
```

Result:

```text
178 passed, 1 warning
```

The warning is the existing Google GenAI dependency deprecation warning. No
new diagnostics were reported in the changed Python files.

---

## 6. Limitations and Scope

- This is deterministic priority weighting, not a CVSS implementation.
- It does not claim that every active alert is a confirmed exploitable
  vulnerability; ZAP confidence and the LLM true-positive assessment still
  remain visible.
- The current CLI still needs direct ZAP/orchestrator wiring and real Juice
  Shop validation.
- Report-specific visual treatment of confirmed versus potential findings is a
  later reporting integration task.

---

## 7. Next Task

Use the new score and posture fields in the real ZAP/Juice Shop integration,
then validate that the Day 36 LLM output and reports preserve the distinction
between confirmed active evidence and potential passive observations.

**Commit-ready files:** `sentinelai/checks/base.py`, `sentinelai/checks/orchestrator.py`, `sentinelai/checks/__init__.py`, `tests/test_day39_risk_weighting.py`, `WEEK_6_DAY_39_REPORT.md`

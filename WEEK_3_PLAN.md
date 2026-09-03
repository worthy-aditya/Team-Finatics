# Week 3 Implementation Plan - Windows Event Logs & LLM Pipeline
**Dates:** 2026-08-19 to 2026-08-25 (Days 15-21)
**Developer:** Affan Shaikh (Security Tools & Scanning Engine)
**Objective:** Integrate Windows Event Logs into CLI and connect to LLM analysis

---

## Week 3 Strategy Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  SentinelAI Week 3 Pipeline                  │
└─────────────────────────────────────────────────────────────┘

Windows Event Log (Security Log)
        ↓
PyWin32 Provider (Read)
        ↓
Event Filter (Critical Event IDs: 4624, 4625, 4720, etc.)
        ↓
Event Parser (Structured Dict Format)
        ↓
CLI Integration (--logs command)
        ↓
LLM Analysis (Aditya's prompt_engine)
        ↓
Security Recommendations
        ↓
User Approval (Human-in-Loop)
        ↓
Final Report
```

### Task Breakdown by Day

#### **Day 15: Set up PyWin32 & Basic Log Reading**
- Install pywin32 library
- Initialize Windows Event Log reader
- Test reading Security log
- Output raw events to terminal
- **Deliverable:** Event log entries printing to terminal

#### **Day 16: Filter for Critical Event IDs**
- Implement event ID filtering (4624, 4625, 4720, 4726, 4768, 4771, 5140)
- Build threshold-based alerting (e.g., 5+ failed logins = suspicious)
- Create anomaly detection logic
- **Deliverable:** Filtered log reader with critical events only

#### **Day 17: Build Event Log Parser**
- Create structured output: EventID, timestamp, user, IP, source
- Parse extra event data fields
- Build deduplication logic
- Create summary statistics
- **Deliverable:** Parsed events in structured dict format

#### **Day 18: CLI Integration (`--logs` command)**
- Add new command: `sentinelai logs`
- Connect to event log provider
- Implement output formatting
- Add time window filtering
- **Deliverable:** `sentinelai logs` returns parsed events

#### **Day 19: LLM Integration**
- Pass parsed events to prompt_engine
- Generate threat assessments
- Create security recommendations
- Build action items list
- **Deliverable:** `sentinelai logs --analyze` pipeline working

#### **Day 20: Human-in-Loop Approval**
- Add user confirmation prompts
- Build approval workflow
- Implement safety checks
- Add confirmation for sensitive operations
- **Deliverable:** User prompted before executing actions

#### **Day 21: Team Sync & Demo**
- Comprehensive documentation
- Full pipeline demonstration
- Code review preparation
- Merge to affan branch
- **Deliverable:** Complete Week 3 with all tasks done

---

## Implementation Approach

### Phase 1: Core Event Log Reading (Days 15-17)

**Dependencies:**
```
Windows 10/Server 2016+
Python 3.8+
pywin32 library (install via pip)
Administrative privileges (for Security log)
```

**Key Classes to Build:**
```python
class EventLogReader:
    """Read from Windows Event Logs"""
    
class EventFilter:
    """Filter events by ID and criteria"""
    
class EventParser:
    """Parse raw events into structured format"""
    
class EventAnalyzer:
    """Analyze events for threats"""
```

### Phase 2: CLI Integration (Days 18-19)

**New CLI Command:**
```bash
# Basic usage
sentinelai logs                          # Last 24 hours

# With filters
sentinelai logs --hours 48              # Last 48 hours
sentinelai logs --event-ids 4625        # Only failed logins
sentinelai logs --json                  # JSON output
sentinelai logs --analyze               # With LLM analysis

# Combined scanning
sentinelai scan --target 127.0.0.1 --logs  # Scan + logs together
```

### Phase 3: User Safety (Days 20-21)

**Approval Workflow:**
```
User runs: sentinelai scan --target 192.168.1.100

Display: Summary of what will happen
Prompt: "Confirm scan on 192.168.1.100? (y/n)"

If Y → Execute scan
If N → Cancel operation
```

---

## Data Structures

### Event Log Entry (Parsed Format)
```python
{
    "event_id": 4625,
    "event_type": "Warning",
    "timestamp": "2026-08-18T14:30:00",
    "source": "Microsoft-Windows-Security-Auditing",
    "computer": "DESKTOP-USER",
    "user": "DOMAIN\\TestUser",
    "ip_address": "192.168.1.50",
    "description": "Failed logon attempt - Bad password",
    "additional_data": {
        "logon_type": 3,
        "failure_count": 5,
        "process_name": "svchost.exe"
    },
    "risk_level": "MEDIUM",
    "mitre_mapping": ["T1110 - Brute Force"]
}
```

### Analysis Output (LLM Format)
```python
{
    "analysis_type": "event_log_analysis",
    "scan_timestamp": "2026-08-18T14:45:00",
    "events_analyzed": 1250,
    "critical_events": 5,
    "findings": [
        {
            "finding": "Multiple failed logon attempts",
            "severity": "HIGH",
            "count": 7,
            "affected_users": ["DOMAIN\\TestUser"],
            "recommendation": "Review user credentials and enable MFA"
        }
    ],
    "threat_summary": "MEDIUM - Possible brute force attack detected",
    "actions_recommended": [...]
}
```

---

## Testing Strategy

### Unit Tests
- Test event log reader initialization
- Test event filtering logic
- Test parsing functions
- Test edge cases

### Integration Tests
- Full pipeline: Read → Filter → Parse → Analyze
- LLM integration
- CLI command execution

### Manual Testing Scenarios
1. **Scenario A:** Normal user activity (baseline)
2. **Scenario B:** Suspicious activity (multiple failed logins)
3. **Scenario C:** Account creation/deletion events
4. **Scenario D:** Network access patterns

---

## Success Criteria

✅ **Day 15:** Can read Security log entries (at least 10 events)
✅ **Day 16:** Can filter to only critical events (5 events max)
✅ **Day 17:** Can parse into structured format with all key fields
✅ **Day 18:** CLI command works: `sentinelai logs` outputs events
✅ **Day 19:** LLM analysis pipeline functioning
✅ **Day 20:** User approval prompt working
✅ **Day 21:** Full pipeline demo + documentation complete

---

## Risk Mitigation

### Risk 1: Admin Privileges Required
**Mitigation:**
- Clear error message if not running as admin
- Fallback to mock data for demo
- Documentation on elevation

### Risk 2: Large Event Logs
**Mitigation:**
- Implement time window filtering
- Batch processing
- Caching strategy

### Risk 3: API Call Limits
**Mitigation:**
- Use mock analysis initially
- Rate limiting
- Batch processing for LLM

---

## Deliverables Summary

| Day | Deliverable | Files |
|-----|-------------|-------|
| 15 | Event log reader functional | `sentinelai/event_logs.py` (enhanced) |
| 16 | Filtered event capture | Updated `event_logs.py` |
| 17 | Structured parser | Updated `event_logs.py` |
| 18 | CLI `--logs` command | Updated `sentinelai/cli.py` |
| 19 | LLM analysis pipeline | Updated `prompt_engine.py` |
| 20 | Approval workflow | Updated `cli.py` |
| 21 | Full documentation + demo | `WEEK_3_COMPLETION_REPORT.md` |

---

## Resource Requirements

- **Time per day:** 4-6 hours (intensive coding)
- **Tools needed:** PyWin32, python-nmap (existing)
- **Access required:** Admin privileges on Windows
- **Dependencies:** Aditya's final LLM implementations

---

## Go/No-Go Decision Points

| Checkpoint | Success Criteria |
|-----------|-----------------|
| After Day 15 | Can read at least 100 events from Security log |
| After Day 16 | Can filter to critical events reliably |
| After Day 17 | Parser output matches expected format 100% |
| After Day 18 | `sentinelai logs` command executes without errors |
| After Day 19 | LLM receives event data and returns analysis |
| After Day 20 | Approval prompts work correctly |
| After Day 21 | Full pipeline demo successful |

**Go:** Proceed to each next phase only if success criteria met
**No-Go:** Pause and fix issues before proceeding

---

## Next Actions

1. ✅ Understand the Week 3 strategy (this document)
2. 🔄 Start Day 15: Install PyWin32 and build event log reader
3. 📋 Follow daily checklist for each day
4. 🧪 Test each component before moving to next day
5. 📝 Document findings and blockers daily

Ready to begin Week 3 implementation?

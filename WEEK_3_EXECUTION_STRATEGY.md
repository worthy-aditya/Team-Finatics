# Week 3 Execution Strategy - Detailed Approach
**Created:** 2026-08-18
**Status:** Ready to Execute

---

## WHAT I'LL BE DOING IN WEEK 3

### Overview
Week 3 focuses on integrating **Windows Event Logs** into SentinelAI and connecting them to the LLM analysis pipeline. This adds a second major data source for security intelligence beyond just network scanning.

### The Big Picture
```
Week 1 (Days 1-7):    Built core Nmap scanner ✅
Week 2 (Days 8-14):   Integrated CLI + LLM framework ✅
Week 3 (Days 15-21):  Add Windows Event Logs + Full Pipeline 🔄
```

---

## 7-DAY BREAKDOWN WITH HOW I'LL DO IT

### **DAY 15: PyWin32 Setup & Event Log Reader**

**What I'm doing:**
- Installing PyWin32 library (Windows event log access library)
- Creating EventLogReader class to connect to Windows Security log
- Writing code to read the last 1,000 events from your computer's Security log
- Testing that raw event data is being captured correctly

**How I'm doing it:**
```python
# Step 1: Install pywin32
pip install pywin32
python -m pywin32_postinstall -install  # Post-install script

# Step 2: Create EventLogReader class that:
class EventLogReader:
    def open_log(self, log_name="Security"):
        # Connect to Windows Event Log
        
    def read_events(self, max_count=1000):
        # Read raw events from log
        
    def get_event_fields(self, event):
        # Extract fields: EventID, timestamp, source, etc.

# Step 3: Test with real data
events = reader.read_events()
print(f"Read {len(events)} events from Security log")
for event in events[:10]:
    print(f"Event {event['event_id']}: {event['timestamp']}")
```

**Deliverable:** 
- Event log entries printing to terminal
- File: Enhanced `sentinelai/event_logs.py`

**Success Check:** 
✅ Can read at least 100 events from your Windows Security log

---

### **DAY 16: Critical Event Filtering**

**What I'm doing:**
- Building event filtering logic to only show critical security events
- Capturing specific Event IDs: 4624 (login), 4625 (failed login), 4720 (new user), etc.
- Implementing threshold-based detection (e.g., 5+ failed logins = alert)
- Creating anomaly detection for suspicious patterns

**How I'm doing it:**
```python
# Step 1: Define critical event IDs
CRITICAL_EVENTS = {
    4624: "Successful Logon",
    4625: "Failed Logon",       # Alert if > 5 in 1 hour
    4720: "User Created",        # Alert always
    4726: "User Deleted",        # Alert always
    4768: "Kerberos TGT",
    4771: "Kerberos Failed",     # Alert if > 10 in 1 hour
    5140: "Network Share Access"
}

# Step 2: Build EventFilter class
class EventFilter:
    def filter_critical(self, events):
        # Keep only events in CRITICAL_EVENTS
        
    def detect_brute_force(self, events):
        # Count failed logins (Event 4625)
        # If > 5 in 1 hour → ALERT
        
    def detect_account_changes(self, events):
        # Track account creation/deletion
        # If unexpected → ALERT

# Step 3: Test filtering
critical_events = filter.filter_critical(all_events)
print(f"Found {len(critical_events)} critical events")
print(filter.detect_brute_force(all_events))
```

**Deliverable:**
- Filtered log reader returning only critical events
- File: Updated `sentinelai/event_logs.py`

**Success Check:**
✅ Can filter raw events to ~5-20 critical events per day

---

### **DAY 17: Event Log Parser**

**What I'm doing:**
- Converting raw Windows event data into structured format
- Extracting key fields: EventID, timestamp, user, IP, source, description
- Building JSON serialization for later use
- Creating deduplication logic (same event shouldn't be counted twice)
- Adding event summary statistics

**How I'm doing it:**
```python
# Step 1: Create EventParser class
class EventParser:
    def parse_event(self, raw_event):
        # Convert raw Windows event to dict:
        return {
            "event_id": 4625,
            "timestamp": "2026-08-18T14:30:00",
            "user": "DOMAIN\\TestUser",
            "ip_address": "192.168.1.50",
            "computer": "DESKTOP-USER",
            "description": "Failed logon - bad password",
            "severity": "MEDIUM"
        }
    
    def parse_batch(self, events):
        # Parse all events in batch
        # Remove duplicates
        # Add summary statistics

# Step 2: Test parsing
parsed = parser.parse_batch(critical_events)
print(json.dumps(parsed, indent=2))

# Output should look like:
# {
#   "event_id": 4625,
#   "timestamp": "2026-08-18T14:30:00",
#   "user": "DOMAIN\\TestUser",
#   "ip_address": "192.168.1.50",
#   "description": "Failed logon - bad password",
#   "risk_level": "MEDIUM"
# }
```

**Deliverable:**
- Parsed events in structured dict format
- File: Updated `sentinelai/event_logs.py`

**Success Check:**
✅ Parser output matches expected format 100%

---

### **DAY 18: CLI Integration (`--logs` command)**

**What I'm doing:**
- Adding new CLI command: `sentinelai logs`
- Connecting to event log reader/filter/parser
- Implementing output formatting (human-readable, JSON, LLM format)
- Adding time window filtering (last 24 hours, 48 hours, etc.)
- Error handling for permission issues

**How I'm doing it:**
```python
# In cli.py, add new command:

@main.command()
@click.option("--hours", default=24, help="Hours to look back")
@click.option("--event-ids", multiple=True, help="Filter by event ID")
@click.option("--json", "output_json", is_flag=True, help="JSON output")
@click.option("--llm-format", is_flag=True, help="LLM-ready format")
def logs(hours, event_ids, output_json, llm_format):
    """Read and analyze Windows Event Logs"""
    reader = EventLogReader()
    events = reader.read_events(hours_back=hours)
    
    if event_ids:
        events = filter.filter_by_id(events, event_ids)
    
    if llm_format:
        output = format_for_llm(events)
    elif output_json:
        output = json.dumps(events)
    else:
        output = format_human_readable(events)
    
    click.echo(output)
```

**CLI Commands After Day 18:**
```bash
sentinelai logs                    # Last 24 hours, all events
sentinelai logs --hours 48         # Last 48 hours
sentinelai logs --event-ids 4625   # Only failed logins
sentinelai logs --json             # JSON output
sentinelai logs --llm-format       # For LLM analysis
```

**Deliverable:**
- `sentinelai logs` command working
- File: Updated `sentinelai/cli.py`

**Success Check:**
✅ `sentinelai logs` executes without errors and returns events

---

### **DAY 19: LLM Integration & Analysis**

**What I'm doing:**
- Passing parsed event log data to Aditya's `prompt_engine`
- Generating AI-powered threat assessments
- Creating security recommendations based on detected patterns
- Building action item lists for security team

**How I'm doing it:**
```python
# In logs command, add analysis:

if analyze_flag:
    from sentinelai.prompt_engine import PromptEngine
    
    engine = PromptEngine(provider="openai")  # or claude/ollama
    
    # Format events for LLM
    llm_data = format_events_for_llm(events)
    
    # Get analysis
    analysis = engine.analyze_scan_results(llm_data)
    
    # Display results
    print("THREAT ASSESSMENT")
    print(f"Risk Level: {analysis['risk_level']}")
    print(f"Findings: {analysis['findings']}")
    print(f"Recommendations: {analysis['recommendations']}")
```

**Output Example:**
```
THREAT ASSESSMENT
=====================================
Risk Level: MEDIUM

Findings:
- 7 failed logon attempts (user: TestUser)
- 2 user accounts created (no authorization record)
- Network share accessed from unusual IP

Recommendations:
1. Investigate TestUser account - possible compromise
2. Review new account creation - verify with admin
3. Check network share access from 192.168.1.50

Actions:
- [ ] Reset TestUser password
- [ ] Verify new accounts
- [ ] Review network access logs
```

**Deliverable:**
- Full LLM analysis pipeline working
- File: Updated `prompt_engine.py` + `cli.py`

**Success Check:**
✅ LLM receives event data and returns structured analysis

---

### **DAY 20: Human-in-Loop Approval**

**What I'm doing:**
- Adding confirmation prompts before running scans
- Building approval workflow for sensitive operations
- Implementing safety checks (e.g., "Are you sure?" for destructive actions)
- Creating audit trail of approvals

**How I'm doing it:**
```python
# Before executing any scan:

click.echo("Summary of operation:")
click.echo(f"Target: {target}")
click.echo(f"Scan type: {scan_type}")
click.echo(f"Will scan ports: 1-1000")

if not click.confirm("Proceed with scan?"):
    click.echo("Operation cancelled.")
    return

# Execute scan
result = scanner.scan(target)

# Log approval
audit_log.add_entry(
    user=get_current_user(),
    action="scan",
    target=target,
    approved=True,
    timestamp=datetime.now()
)
```

**User Experience:**
```
$ sentinelai scan --target 192.168.1.100

[*] Scanning target: 192.168.1.100
[*] Scan Type: Standard (-sV -p 1-1000)
[*] Timeout: 60 seconds

========================================
This operation will:
- Scan all ports 1-1000 on 192.168.1.100
- Attempt service identification
- May trigger security alerts/logs
========================================

Proceed with scan? [y/N]: y
[+] Scan started...
```

**Deliverable:**
- User approval prompts working
- File: Updated `sentinelai/cli.py`

**Success Check:**
✅ User prompted and can approve/deny operations

---

### **DAY 21: Team Sync, Comprehensive Demo & Documentation**

**What I'm doing:**
- Writing detailed documentation of all Week 3 work
- Creating comprehensive demonstration showing the full pipeline
- Performing code review and quality checks
- Merging code to `affan` branch
- Creating final completion report

**How I'm doing it:**

**1. Documentation:**
```
WEEK_3_COMPLETION_REPORT.md
- Executive summary
- Day-by-day accomplishments
- Full architecture diagram
- API documentation for other teams
- Troubleshooting guide
```

**2. Full Pipeline Demo:**
```bash
# Demo Scenario: Detect brute force attack in Event Logs

# Step 1: Read event logs
$ sentinelai logs --hours 24 --json
[Shows 1,250 events from last 24 hours]

# Step 2: Filter to critical events
$ sentinelai logs --hours 24 --event-ids 4625
[Shows 7 failed login attempts - ALERT!]

# Step 3: Analyze with LLM
$ sentinelai logs --hours 24 --analyze
[LLM Analysis]
Risk Level: HIGH
Recommendation: Possible brute force attack on TestUser account

# Step 4: Get approval to remediate
Remediation: Reset TestUser password?
Proceed? [y/N]: y
[Executes remediation]
```

**3. Code Quality:**
- Test coverage review
- Performance metrics
- Documentation review
- Security audit

**4. Merge to Branch:**
```bash
git add sentinelai/
git add test_*.py
git add WEEK_3_*.md
git commit -m "Week 3 Complete: Windows Event Logs + LLM Pipeline"
git push origin affan
```

**Deliverable:**
- Complete documentation
- Full pipeline working end-to-end
- Code merged and ready for team
- File: `WEEK_3_COMPLETION_REPORT.md`

**Success Check:**
✅ Full pipeline demo successful with all features working

---

## OVERALL EXECUTION FLOW

```
┌────────────────────────────────────────────────────────┐
│                   WEEK 3 EXECUTION                      │
└────────────────────────────────────────────────────────┘

Day 15: Setup PyWin32
        ↓
Day 16: Filter Critical Events
        ↓
Day 17: Parse to Structured Format
        ↓
Day 18: CLI Integration (--logs command)
        ↓
Day 19: LLM Analysis Pipeline
        ↓
Day 20: User Approval System
        ↓
Day 21: Full Demo + Documentation
        ↓
COMPLETE: Ready for production use
```

---

## KEY SUCCESS FACTORS

### 1. **PyWin32 Installation (Day 15)**
- Most critical dependency
- Requires post-install script
- Needs admin privileges
- If this fails → entire week blocked

### 2. **Event Log Access (Day 16)**
- Security log requires admin
- May need to elevate privileges
- Error handling if not admin

### 3. **LLM Integration (Day 19)**
- Depends on Aditya's implementations
- Mock analysis available as fallback
- Rate limiting considerations

### 4. **Testing (Throughout)**
- Each day has success criteria
- Test before moving to next day
- Document any blockers immediately

---

## INTEGRATION WITH OTHER TEAMS

### Aditya (LLM)
- Will use my parsed event log data
- Event format: `{"event_id": 4625, "user": "...", "timestamp": "...", ...}`
- LLM receives this + generates threat assessment

### Suraj (Reports)
- Will use my structured event log output
- Can generate reports combining Nmap + Event Log data
- Report template: Scan findings + Security alerts + Recommendations

### Sneha (Testing)
- Will write tests for my event log functions
- Framework mapping for MITRE/OWASP
- End-to-end integration tests

---

## RISK & MITIGATION SUMMARY

| Risk | Impact | Mitigation |
|------|--------|-----------|
| PyWin32 won't install | CRITICAL | Use fallback mock data |
| No admin privileges | CRITICAL | Clear error message + guide to elevate |
| Large event logs | MEDIUM | Implement time-window filtering |
| LLM API failures | MEDIUM | Mock analysis + queuing |
| Windows version issues | LOW | Test on multiple versions |

---

## TIMELINE ESTIMATE

- **Day 15:** 2-3 hours (setup + basic reading)
- **Day 16:** 2-3 hours (filtering logic)
- **Day 17:** 2-3 hours (parsing)
- **Day 18:** 2-3 hours (CLI integration)
- **Day 19:** 2-3 hours (LLM pipeline)
- **Day 20:** 1-2 hours (approval workflow)
- **Day 21:** 2-3 hours (demo + documentation)

**Total:** 15-20 hours of focused work across 7 days

---

## READY TO BEGIN?

All planning is complete. Ready to execute Week 3 starting with Day 15 implementation.

Shall I proceed with Day 15: PyWin32 Setup & Event Log Reader?

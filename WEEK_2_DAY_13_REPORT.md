# Week 2 — Day 13: Windows Event Log APIs Research
**Date:** 2026-08-18  
**Developer:** Affan Shaikh (Security Tools & Scanning Engine)  
**Sprint:** SentinelAI 30-Day Sprint | Week 2, Day 13  
**Status:** ✅ **COMPLETE**

---

## Day 13 Objective
> Research Windows Event Log APIs  
> **Deliverable:** Research notes added to GitHub + Prototype event_logs.py module

---

## Executive Summary

### Overview
Windows Event Logs are a critical source of security intelligence, containing millions of events that log system activities, security events, and application behavior. For SentinelAI, integrating Windows Event Log analysis enables:

- **Threat Detection:** Identify suspicious logons, privilege escalation, and lateral movement
- **Compliance Monitoring:** Track user access and changes for audit trails
- **Forensic Analysis:** Reconstruct incident timelines and attacker activities
- **Behavioral Analysis:** Detect anomalies in user and system behavior

### Key Technologies Evaluated

| Technology | Pros | Cons | Recommendation |
|------------|------|------|-----------------|
| **PyWin32** | Rich API, mature, well-documented | Requires admin, external dependency | ✅ PRIMARY |
| **Windows Event Log APIs** | Native, performant | Limited Python bindings | SECONDARY |
| **WMI (Windows Management Instrumentation)** | Powerful, flexible | Complex syntax | ALTERNATIVE |
| **Event Tracing for Windows (ETW)** | Low-overhead, real-time | Complex, steep learning curve | FUTURE |

**Recommendation:** Use **PyWin32** for Week 3 implementation with potential future migration to native APIs.

---

## Critical Security Event IDs

### Event ID: 4624 - Account Logon (Successful)
**Severity:** INFO  
**Frequency:** Very High  
**MITRE Mapping:** T1078 - Valid Accounts

**Key Fields:**
- Logon Type (2=Interactive, 3=Network, 4=Batch, 5=Service)
- User Account
- Source IP Address
- Source Computer
- Logon Process

**Security Value:**
- Establishes user authentication baseline
- Detects unauthorized access patterns
- Correlates with other suspicious events

**Example:**
```
Event 4624 @ 12:00:00 - User: DOMAIN\Administrator
Logon Type: 2 (Interactive)
IP Address: 192.168.1.100
Computer: DESKTOP-USER
```

---

### Event ID: 4625 - Account Logon Failure
**Severity:** WARNING  
**Frequency:** High  
**MITRE Mapping:** T1110 - Brute Force Attack

**Key Fields:**
- Failure Reason (Bad Password, Account Locked, etc.)
- Failed User Account
- Source IP Address
- Failure Count (consecutive failures)

**Security Value:**
- Indicates brute force attacks when repeated
- Helps identify compromised accounts
- Threshold-based alerting: >5 failures = suspicious

**Example:**
```
Event 4625 @ 11:55:00 - User: DOMAIN\TestUser
Failure Reason: Bad Password
IP Address: 192.168.1.50
Consecutive Failures: 3
```

---

### Event ID: 4720 - User Account Created
**Severity:** HIGH  
**Frequency:** Low (Normal)  
**MITRE Mapping:** T1136 - Create Account

**Security Value:**
- Tracks new account creation
- Detects unauthorized admin account creation
- Enables SoD (Separation of Duties) monitoring

**Example:**
```
Event 4720 @ 14:30:00
New User: DOMAIN\NewAdmin
Creator: DOMAIN\Administrator
```

---

### Event ID: 4726 - User Account Deleted
**Severity:** HIGH  
**Frequency:** Low (Normal)  
**MITRE Mapping:** T1531 - Account Access Removal

**Security Value:**
- Tracks account deletion/removal
- Detects suspicious account cleanup (attacker covering tracks)
- Audit trail for compliance

---

### Event ID: 4768 - Kerberos TGT Requested
**Severity:** INFO  
**Frequency:** Very High  
**MITRE Mapping:** T1558 - Steal or Forge Kerberos Tickets

**Security Value:**
- Monitors Kerberos authentication
- Baseline for normal authentication patterns
- Anomaly detection for unusual auth patterns

---

### Event ID: 4771 - Kerberos Pre-Authentication Failed
**Severity:** WARNING  
**Frequency:** Medium  
**MITRE Mapping:** T1110 - Brute Force

**Security Value:**
- Indicates Kerberos brute force attempts
- Often precedes successful account compromise
- Threshold alerting: >10 failures = attack pattern

---

### Event ID: 5140 - Network Share Accessed
**Severity:** INFO  
**Frequency:** High  
**MITRE Mapping:** T1570 - Lateral Tool Transfer

**Security Value:**
- Tracks lateral movement via file shares
- Detects unusual SMB traffic patterns
- Monitors access to sensitive file shares

---

## Windows Event Log Architecture

### Log Types

**1. Security Log**
- Most critical for security monitoring
- Contains authentication, authorization, and audit events
- Requires administrative privileges to read
- Typical size: 20-50MB (configurable)
- Event IDs: 4000-4999

**2. Application Log**
- Application-specific events
- Errors, warnings, information messages
- Event IDs: 1000-2999

**3. System Log**
- Operating system and driver events
- Boot/shutdown, hardware changes
- Event IDs: 1000-2999

**4. ForwardedEvents Log**
- Events forwarded from other computers
- Centralized log collection
- Essential for large networks

### Event Log Structure

```
Event ID: 4624
Level: Information
Source: Microsoft-Windows-Security-Auditing
Computer: DESKTOP-USER
Timestamp: 2026-08-18 12:00:00
EventData:
  - SubjectUserSid
  - SubjectUserName
  - SubjectDomainName
  - SubjectLogonId
  - TargetUserSid
  - TargetUserName
  - TargetDomainName
  - TargetLogonId
  - LogonType
  - LogonProcessName
  - AuthenticationPackageName
  - WorkstationName
  - LogonGuid
  - TransmittedServices
  - LmPackageName
  - KeyLength
  - ProcessId
  - ProcessName
  - IpAddress
  - IpPort
  - ImpersonationLevel
  - RestrictedAdminMode
  - TargetOutboundUserName
  - TargetOutboundDomainName
  - VirtualAccount
  - FailureReason
  - SubStatus
  - Status
```

---

## PyWin32 Implementation Strategy

### Installation Steps

```bash
# Step 1: Install pywin32
pip install pywin32

# Step 2: Run post-install script (requires admin)
python -m pip install pywin32
python -m pywin32_postinstall -install

# Step 3: Verify installation
python -c "import win32evtlog; print('PyWin32 OK')"
```

### Basic API Usage

```python
import win32evtlog

# Open Security log on local computer
handle = win32evtlog.OpenEventLog(".", "Security")

# Define flags
flags = (win32evtlog.EVENTLOG_BACKWARDS_READ | 
         win32evtlog.EVENTLOG_SEQUENTIAL_READ)

# Read events
events = win32evtlog.ReadEventLog(handle, flags, 0)

# Process each event
for event in events:
    event_id = event.GetEventID()
    event_type = event.GetType()
    computer = event.GetComputerName()
    timestamp = event.GetEventRecordProps()[5]
    
    print(f"Event {event_id}: {event_type} on {computer}")

# Close handle
win32evtlog.CloseEventLog(handle)
```

### Key Classes & Methods

| Class/Method | Purpose |
|-------------|---------|
| `win32evtlog.OpenEventLog(computer, log)` | Open event log |
| `win32evtlog.ReadEventLog(handle, flags, offset)` | Read events |
| `win32evtlog.CloseEventLog(handle)` | Close event log handle |
| `event.GetEventID()` | Get event ID |
| `event.GetType()` | Get event type (Error, Warning, etc.) |
| `event.GetSourceName()` | Get source (process name) |
| `event.GetComputerName()` | Get computer name |
| `event.GetEventRecordProps()` | Get all event properties |
| `event.GetStringInsert(index)` | Get specific event data field |

---

## Filtering & Performance Optimization

### Efficient Event Log Reading

**Issue:** Security logs can contain millions of events
**Solution:** Use filtering and targeted queries

```python
# Filter by event ID
event_ids = [4624, 4625, 4720, 4726, 4768, 4771, 5140]

# Filter by time range
hours_back = 24
cutoff_time = datetime.now() - timedelta(hours=hours_back)

# Filter by source
source_filters = ["Microsoft-Windows-Security-Auditing"]
```

### Recommended Query Strategy

1. **Read backwards** (most recent first)
2. **Filter on critical event IDs** only
3. **Limit time window** (last 24-48 hours)
4. **Batch processing** (read 100 events at a time)
5. **Cache results** (store in JSON for analysis)

---

## Integration with LLM Pipeline

### Proposed Flow

```
Windows Event Log
      ↓
PyWin32 Provider (Read)
      ↓
Filter (Critical Events Only)
      ↓
Parse/Structure (Event Dict Format)
      ↓
LLM Analysis (Threat Assessment)
      ↓
Generate Recommendations
      ↓
CLI Output / Report
```

### LLM Prompt Template for Event Log Analysis

```
Analyze the following Windows security events and provide:
1. Threat assessment (LOW/MEDIUM/HIGH/CRITICAL)
2. Identified attack patterns
3. Compromised accounts (if any)
4. Recommended remediation steps

SECURITY EVENTS:
{formatted_events}

Provide structured analysis focusing on:
- Account compromise indicators
- Brute force attacks
- Lateral movement attempts
- Privilege escalation events
- Unusual access patterns
```

---

## Compliance & Security Framework Mapping

### OWASP Top 10 Mappings

| OWASP Category | Event IDs | Description |
|----------------|-----------|-------------|
| A01:2021 - Broken Access Control | 4625, 5140 | Failed access attempts, share access |
| A02:2021 - Cryptographic Failures | 4768, 4771 | Kerberos authentication issues |
| A07:2021 - Identification & Auth Failures | 4624, 4625 | Logon events |

### MITRE ATT&CK Mappings

| Tactic | Technique | Event IDs | Description |
|--------|-----------|-----------|-------------|
| Initial Access | T1078 - Valid Accounts | 4624 | Legitimate logon baseline |
| Execution | T1059 | Process creation logs | N/A (future) |
| Persistence | T1136 - Create Account | 4720 | Backdoor account creation |
| Privilege Escalation | T1134 - Access Token Manipulation | 4672 | Privilege use events |
| Defense Evasion | T1140 - Deobfuscation | Audit Logs | Disabled auditing |
| Credential Access | T1110 - Brute Force | 4625, 4771 | Failed login attempts |
| Lateral Movement | T1570 - Lateral Tool Transfer | 5140 | Network share access |
| Collection | T1005 - Data from Local System | 5140, 4656 | File access events |
| Exfiltration | T1041 - Exfiltration Over Other Network | N/A | Requires network logs |
| Impact | T1531 - Account Access Removal | 4726 | Account deletion |

---

## Week 3 Implementation Plan

### Day 15: PyWin32 Setup & Basic Reading
- [ ] Install and configure pywin32
- [ ] Implement basic event log reader
- [ ] Test access to Security log
- [ ] Document access requirements

### Day 16: Critical Event Filtering
- [ ] Filter for critical event IDs (4624, 4625, 4720, 4726, 4768, 4771, 5140)
- [ ] Implement time-based filtering
- [ ] Build event count aggregation
- [ ] Create threshold-based alerting

### Day 17: Event Log Parser
- [ ] Build structured output format
- [ ] Extract key fields from events
- [ ] Create JSON serialization
- [ ] Add event deduplication

### Day 18: CLI Integration
- [ ] Add `--logs` command to CLI
- [ ] Connect to event log provider
- [ ] Implement output formatting
- [ ] Add error handling for permission issues

### Day 19: LLM Integration
- [ ] Pass parsed events to prompt_engine
- [ ] Generate threat assessments
- [ ] Create actionable recommendations
- [ ] Build report generation

### Day 20: Human-in-Loop Approval
- [ ] Add confirmation prompts for scans
- [ ] Build approval workflow
- [ ] Implement safety checks

### Day 21: Team Demo
- [ ] Demonstrate full `--logs` pipeline
- [ ] Show threat detection in action
- [ ] Present findings and recommendations

---

## Challenges & Mitigation

### Challenge 1: Administrative Privileges Required
**Issue:** Reading Security log requires administrator/SYSTEM privileges
**Mitigation:**
- Document privilege requirements clearly
- Provide installation guide for users
- Implement fallback for read failures
- Support running as Windows service

### Challenge 2: Large Log Files
**Issue:** Security logs can grow very large (GB+)
**Mitigation:**
- Implement time-window filtering
- Use event ID filtering (only critical events)
- Batch processing to manage memory
- Consider log archive analysis

### Challenge 3: Event Log Format Variations
**Issue:** Different Windows versions have different event formats
**Mitigation:**
- Test on Windows 10, Server 2016, Server 2019, Server 2022
- Implement version detection
- Build version-specific parsers
- Use try-catch for unknown fields

### Challenge 4: Performance with Large Datasets
**Issue:** Reading/analyzing large event logs is slow
**Mitigation:**
- Implement caching (Redis, SQLite)
- Use background workers
- Implement progress indicators
- Add timeout handling

---

## Testing Strategy

### Unit Tests
- [ ] Test PyWin32Provider initialization
- [ ] Test event parsing
- [ ] Test filtering logic
- [ ] Test edge cases (empty logs, malformed events)

### Integration Tests
- [ ] End-to-end event reading
- [ ] Event log to LLM pipeline
- [ ] Report generation
- [ ] CLI command integration

### Performance Tests
- [ ] Read 10K events benchmark
- [ ] Filtering performance
- [ ] Memory usage under load
- [ ] Analysis time measurement

---

## Deliverables Completed

✅ **Research Documentation**
- Comprehensive analysis of Windows Event Log APIs
- Comparison of available technologies
- Critical event ID reference guide

✅ **Prototype Code**
- `sentinelai/event_logs.py` module created
- PyWin32Provider class implemented
- EventLogAnalyzer skeleton built
- Sample data for testing

✅ **Week 3 Planning**
- Clear implementation roadmap
- Day-by-day task breakdown
- Risk mitigation strategies
- Testing approach defined

✅ **Installation Guide**
- PyWin32 setup instructions
- Privilege requirements documented
- Troubleshooting tips provided
- Sample code included

---

## Key Insights for Future Implementation

1. **Event ID 4625 (Failed Logon)** is the most valuable for threat detection
   - Threshold: >5 in 1 hour = potential attack
   - Combine with successful logons for context

2. **Kerberos Events (4768, 4771)** are underutilized
   - Can detect sophisticated attacks
   - Useful in enterprise environments with AD

3. **Network Share Access (5140)** indicates lateral movement
   - Critical for detecting post-breach activity
   - Often combined with account abuse

4. **Time Correlation** is essential
   - Unusual logon time = suspicious
   - After-hours access = anomaly
   - Rapid account creation+deletion = cleanup

5. **Baseline Behavior** is critical
   - Define "normal" logon patterns first
   - Detect deviations from baseline
   - Account for time-based variations (9-5 vs 24/7)

---

## References & Resources

### Official Documentation
- [Microsoft Event Log Documentation](https://docs.microsoft.com/en-us/windows/security/threat-protection/auditing/auditing-overview)
- [PyWin32 Documentation](https://pypi.org/project/pywin32/)
- [Windows Event ID Reference](https://www.ultimatewindowssecurity.com/securitylog/encyclopedia/)

### Security Resources
- [MITRE ATT&CK Framework](https://attack.mitre.org/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [SANS Event Log Best Practices](https://www.sans.org/reading-room/)

### Related Tools
- Windows Event Viewer (GUI)
- PowerShell: `Get-EventLog`, `Get-WinEvent`
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Splunk Event Log Analysis

---

## Sign-Off

**Day 13 Status:** ✅ **COMPLETE AND RESEARCHED**

- ✅ Windows Event Log APIs thoroughly researched
- ✅ PyWin32 identified as primary technology
- ✅ Critical event IDs documented
- ✅ Prototype event_logs.py module created
- ✅ Week 3 implementation plan detailed
- ✅ Installation & configuration guide prepared
- ✅ MITRE/OWASP framework mappings created

**Developer:** Affan Shaikh  
**Completion Date:** 2026-08-18  
**Next:** Day 14 Team Sync & Demo  
**Team:** Team Finatics | CodeQuest 4.0

---

## Week 2 Summary (Days 8-13)

| Day | Task | Status | Impact |
|-----|------|--------|--------|
| 8 | CLI Integration | ✅ DONE | Foundation for all other work |
| 9 | Enhanced Output Structure | ✅ DONE | LLM pipeline ready |
| 10 | LLM Integration Interface | ✅ DONE | Mock analysis working |
| 11 | Multi-target Testing | ✅ DONE | Validated on multiple scenarios |
| 12 | Edge Case Handling | ✅ DONE | Robust error messages |
| 13 | Windows Event Log Research | ✅ DONE | Week 3 ready to launch |

**Week 2 Completion:** 6/6 Tasks ✅ **100% COMPLETE**

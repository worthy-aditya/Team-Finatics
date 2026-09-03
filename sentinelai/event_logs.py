"""
Windows Event Log Integration Research & Prototype
Day 13: Research Windows Event Log APIs for SentinelAI

This module researches and prototypes Windows Event Log access for 
security event analysis and LLM-based threat detection.
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from abc import ABC, abstractmethod


class WindowsEventLogProvider(ABC):
    """Abstract base class for Windows Event Log providers"""
    
    @abstractmethod
    def read_logs(self, log_name: str, filters: Optional[Dict] = None) -> List[Dict]:
        """Read events from Windows Event Log"""
        pass
    
    @abstractmethod
    def get_log_names(self) -> List[str]:
        """Get available event log names"""
        pass


class PyWin32Provider(WindowsEventLogProvider):
    """
    PyWin32-based Windows Event Log provider
    
    Requirements:
    - pywin32 library (pip install pywin32)
    - Windows administrative privileges
    
    Key Features:
    - Access to Security, Application, System logs
    - Real-time log reading
    - Event filtering by ID and level
    - Large-scale log analysis
    
    Documentation: https://pypi.org/project/pywin32/
    """
    
    # Critical Security Event IDs
    CRITICAL_EVENT_IDS = {
        4624: "Account Logon",
        4625: "Account Logon Failure",
        4720: "User Account Created",
        4722: "User Account Enabled",
        4723: "Password Changed",
        4724: "Password Reset",
        4725: "User Account Disabled",
        4726: "User Account Deleted",
        4768: "Kerberos Auth Service Ticket Requested",
        4769: "Kerberos Service Ticket Requested",
        4770: "Kerberos Service Ticket Renewed",
        4771: "Kerberos Pre-Authentication Failed",
        4776: "NTLM Authentication Succeeded",
        4777: "NTLM Authentication Failed",
        4797: "Audit Policy Change",
        4798: "User or Group Membership Changed",
        4799: "Security Group Enumeration",
        4964: "Special Groups assigned to new logon",
        5140: "Network Share Accessed",
        5145: "Network Share File Accessed",
    }
    
    def __init__(self):
        """Initialize PyWin32 provider"""
        self.available = self._check_availability()
        self.computer = "."  # Local computer
    
    def _check_availability(self) -> bool:
        """Check if pywin32 is available and configured"""
        try:
            import win32evtlog
            return True
        except ImportError:
            return False
    
    def get_log_names(self) -> List[str]:
        """Get available event log names"""
        if not self.available:
            return []
        
        try:
            import win32evtlog
            # Common Windows event logs
            return [
                "Security",
                "Application",
                "System",
                "ForwardedEvents",
                "PowerShell",
            ]
        except Exception as e:
            print(f"Error getting log names: {e}")
            return []
    
    def read_logs(self, log_name: str = "Security", filters: Optional[Dict] = None) -> List[Dict]:
        """
        Read events from Windows Event Log
        
        Args:
            log_name: Name of event log to read ("Security", "Application", etc.)
            filters: Optional filter dict with keys:
                - event_ids: List of event IDs to filter
                - hours_back: Number of hours to look back
                - event_type: "Error", "Warning", "Information"
        
        Returns:
            List of parsed event dictionaries
        """
        if not self.available:
            print("PyWin32 not available. Install with: pip install pywin32")
            return []
        
        try:
            import win32evtlog
            
            events = []
            flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
            
            try:
                handle = win32evtlog.OpenEventLog(self.computer, log_name)
            except Exception as e:
                print(f"Cannot open log '{log_name}': {e}")
                print("Note: Security log requires administrator privileges")
                return []
            
            # Default: read last 1000 events
            while True:
                events_batch = win32evtlog.ReadEventLog(handle, flags, 0)
                if not events_batch:
                    break
                
                for event in events_batch:
                    parsed_event = self._parse_event(event, log_name)
                    
                    # Apply filters if provided
                    if filters:
                        if not self._apply_filters(parsed_event, filters):
                            continue
                    
                    events.append(parsed_event)
            
            win32evtlog.CloseEventLog(handle)
            return events
            
        except Exception as e:
            print(f"Error reading logs: {e}")
            return []
    
    def _parse_event(self, event, log_name: str) -> Dict:
        """Parse a single event from pywin32"""
        try:
            event_id = event.EventID & 0xFFFF
            message = ""
            if event.StringInserts:
                try:
                    message = " | ".join(event.StringInserts[:3])
                except:
                    pass
            
            return {
                "log": log_name,
                "event_id": event_id,
                "event_type": event.EventType,
                "source": event.SourceName,
                "computer": event.ComputerName,
                "timestamp": str(event.TimeGenerated),
                "message": message,
                "category": event.EventCategory,
                "record_number": event.RecordNumber
            }
        except Exception as e:
            print(f"Error parsing event: {e}")
            return {}
    
    def _apply_filters(self, event: Dict, filters: Dict) -> bool:
        """Apply filters to event"""
        # Filter by event ID
        if "event_ids" in filters:
            if event.get("event_id") not in filters["event_ids"]:
                return False
        
        # Filter by event type
        if "event_type" in filters:
            if event.get("event_type") != filters["event_type"]:
                return False
        
        return True


class EventLogsProvider(WindowsEventLogProvider):
    """
    Windows 'EventLogs' module provider (alternative to PyWin32)
    
    Requirements:
    - Windows native module (no pip install needed)
    - Administrative privileges
    - Python 3.8+
    
    Advantages:
    - No external dependencies
    - Part of Windows SDK
    - Native performance
    
    Note: This is a research placeholder for Week 3 implementation
    """
    
    def __init__(self):
        """Initialize EventLogs provider"""
        self.available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if EventLogs module is available"""
        try:
            # This would use: import wmi or ctypes for native Windows APIs
            return True
        except ImportError:
            return False
    
    def get_log_names(self) -> List[str]:
        """Get available event log names"""
        return ["Security", "Application", "System", "ForwardedEvents"]
    
    def read_logs(self, log_name: str, filters: Optional[Dict] = None) -> List[Dict]:
        """Read events from Windows Event Log - TO BE IMPLEMENTED"""
        return []


# Critical Event ID Analysis
CRITICAL_SECURITY_EVENTS = {
    4624: {
        "name": "Successful Account Logon",
        "severity": "INFO",
        "mitre_mapping": "T1078 - Valid Accounts",
        "description": "User successfully logged in to the system"
    },
    4625: {
        "name": "Failed Account Logon",
        "severity": "WARNING",
        "mitre_mapping": "T1110 - Brute Force",
        "description": "Failed login attempt - may indicate brute force attack"
    },
    4720: {
        "name": "User Account Created",
        "severity": "HIGH",
        "mitre_mapping": "T1136 - Create Account",
        "description": "New user account created on system"
    },
    4726: {
        "name": "User Account Deleted",
        "severity": "HIGH",
        "mitre_mapping": "T1531 - Account Access Removal",
        "description": "User account deleted from system"
    },
    4768: {
        "name": "Kerberos Authentication Ticket Requested",
        "severity": "INFO",
        "mitre_mapping": "T1558 - Steal or Forge Kerberos Tickets",
        "description": "TGT (Ticket Granting Ticket) requested for authentication"
    },
    4771: {
        "name": "Kerberos Pre-Authentication Failed",
        "severity": "WARNING",
        "mitre_mapping": "T1110 - Brute Force",
        "description": "Failed Kerberos authentication - possible password guessing"
    },
    5140: {
        "name": "Network Share Accessed",
        "severity": "INFO",
        "mitre_mapping": "T1570 - Lateral Tool Transfer",
        "description": "Network share access attempt"
    }
}


# Sample Event Log Data (for testing without admin access)
SAMPLE_SECURITY_EVENTS = [
    {
        "log": "Security",
        "event_id": 4624,
        "event_type": "Information",
        "source": "Microsoft-Windows-Security-Auditing",
        "computer": "DESKTOP-USER",
        "timestamp": "2026-08-18 12:00:00",
        "message": "An account was successfully logged on.",
        "user": "DOMAIN\\Administrator",
        "logon_type": 2,  # Interactive logon
        "ip_address": "127.0.0.1"
    },
    {
        "log": "Security",
        "event_id": 4625,
        "event_type": "Warning",
        "source": "Microsoft-Windows-Security-Auditing",
        "computer": "DESKTOP-USER",
        "timestamp": "2026-08-18 11:55:00",
        "message": "An account failed to log on.",
        "user": "DOMAIN\\TestUser",
        "failure_reason": "Bad Password",
        "ip_address": "192.168.1.100"
    },
    {
        "log": "Security",
        "event_id": 5140,
        "event_type": "Information",
        "source": "Microsoft-Windows-Security-Auditing",
        "computer": "DESKTOP-USER",
        "timestamp": "2026-08-18 11:30:00",
        "message": "A network share object was accessed.",
        "share_name": "\\\\SERVER\\Files",
        "user": "DOMAIN\\Administrator",
        "ip_address": "192.168.1.50"
    }
]


class EventLogAnalyzer:
    """Analyze security events for threats and anomalies"""
    
    def __init__(self):
        self.provider = PyWin32Provider() if PyWin32Provider().available else None
    
    def analyze_security_events(self, events: List[Dict], hours_back: int = 24) -> Dict:
        """
        Analyze security events for threats
        
        Args:
            events: List of event dictionaries
            hours_back: Look back period in hours
        
        Returns:
            Analysis results with threat assessment
        """
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "events_analyzed": len(events),
            "critical_events": [],
            "suspicious_patterns": [],
            "threat_summary": "",
            "recommendations": []
        }
        
        # Analyze for suspicious patterns
        failed_logons = self._count_by_event_id(events, 4625)
        successful_logons = self._count_by_event_id(events, 4624)
        new_accounts = self._count_by_event_id(events, 4720)
        deleted_accounts = self._count_by_event_id(events, 4726)
        
        # Detect patterns
        if failed_logons > 5:
            analysis["suspicious_patterns"].append({
                "pattern": "Multiple Failed Logons",
                "severity": "HIGH",
                "count": failed_logons,
                "recommendation": "Investigate potential brute force attack"
            })
        
        if new_accounts > 0:
            analysis["critical_events"].extend([{
                "event_id": 4720,
                "severity": "HIGH",
                "note": f"{new_accounts} new account(s) created"
            }])
        
        # Generate threat summary
        if analysis["critical_events"] or analysis["suspicious_patterns"]:
            analysis["threat_summary"] = "⚠️ POTENTIAL THREATS DETECTED - Review recommended"
            analysis["recommendations"].append("Review suspicious logon attempts")
            analysis["recommendations"].append("Verify new account creation")
        else:
            analysis["threat_summary"] = "✓ No immediate threats detected"
        
        return analysis
    
    def _count_by_event_id(self, events: List[Dict], event_id: int) -> int:
        """Count occurrences of specific event ID"""
        return sum(1 for e in events if e.get("event_id") == event_id)


class EventLogReader:
    """
    High-level event log reader for SentinelAI
    Wraps PyWin32Provider with convenience methods
    Day 15: Core event log reading functionality
    """
    
    def __init__(self):
        """Initialize reader with PyWin32 provider"""
        self.provider = PyWin32Provider()
        self.last_error = None
    
    def open_log(self, log_name: str = "Security") -> bool:
        """
        Check if log can be opened (validates access)
        
        Args:
            log_name: Event log to open ("Security", "Application", "System")
        
        Returns:
            True if log accessible, False otherwise
        """
        if not self.provider.available:
            self.last_error = "PyWin32 not available - install with: pip install pywin32"
            return False
        
        try:
            import win32evtlog
            handle = win32evtlog.OpenEventLog(".", log_name)
            win32evtlog.CloseEventLog(handle)
            return True
        except PermissionError:
            self.last_error = f"Permission denied accessing {log_name} log - requires administrator"
            return False
        except Exception as e:
            self.last_error = f"Cannot open log '{log_name}': {e}"
            return False
    
    def read_events(self, log_name: str = "Security", max_events: int = 1000, 
                   hours_back: Optional[int] = None, event_ids: Optional[List[int]] = None) -> List[Dict]:
        """
        Read events from Windows Event Log
        
        Args:
            log_name: Event log name ("Security", "Application", "System")
            max_events: Maximum number of events to read (default 1000)
            hours_back: Only read events from last N hours (optional)
            event_ids: Only read specific event IDs (optional)
        
        Returns:
            List of parsed event dictionaries
        
        Example:
            reader = EventLogReader()
            events = reader.read_events("Security", max_events=500)
            print(f"Read {len(events)} events")
        """
        if not self.provider.available:
            self.last_error = "PyWin32 not available"
            return []
        
        try:
            import win32evtlog
            import pywintypes
            
            events = []
            flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
            
            try:
                handle = win32evtlog.OpenEventLog(".", log_name)
            except PermissionError:
                self.last_error = f"Permission denied - requires administrator privileges"
                return []
            except Exception as e:
                self.last_error = f"Cannot open log '{log_name}': {str(e)}"
                return []
            
            # Calculate cutoff time if hours_back specified
            cutoff_time = None
            if hours_back:
                cutoff_time = datetime.now() - timedelta(hours=hours_back)
            
            # Read events in batches
            try:
                while len(events) < max_events:
                    events_batch = win32evtlog.ReadEventLog(handle, flags, 0)
                    if not events_batch:
                        break
                    
                    for raw_event in events_batch:
                        if len(events) >= max_events:
                            break
                        
                        try:
                            parsed = self._parse_event(raw_event, log_name)
                            
                            # Apply filters
                            if cutoff_time and self._parse_timestamp(parsed.get("timestamp")) < cutoff_time:
                                continue
                            
                            if event_ids and parsed.get("event_id") not in event_ids:
                                continue
                            
                            events.append(parsed)
                        except Exception as e:
                            # Skip unparseable events and continue
                            continue
            finally:
                win32evtlog.CloseEventLog(handle)
            
            return events
            
        except Exception as e:
            self.last_error = f"Error reading logs: {str(e)}"
            return []
    
    def _parse_event(self, event, log_name: str) -> Dict:
        """
        Parse a single Windows event into structured format
        
        Args:
            event: PyWin32 event object (PyEventLogRecord)
            log_name: Name of log (for metadata)
        
        Returns:
            Dictionary with event fields
        """
        try:
            # Access event properties directly (not methods)
            event_id = event.EventID & 0xFFFF  # Mask to get event ID
            
            # Convert timestamp to readable format
            timestamp_obj = event.TimeGenerated
            if timestamp_obj:
                timestamp_str = str(timestamp_obj)
            else:
                timestamp_str = datetime.now().isoformat()
            
            # Get string inserts (message) safely
            message = ""
            if event.StringInserts:
                try:
                    message = " | ".join(event.StringInserts[:3])  # First 3 inserts
                except:
                    message = ""
            
            return {
                "log": log_name,
                "event_id": event_id,
                "event_type": event.EventType,
                "source": event.SourceName,
                "computer": event.ComputerName,
                "timestamp": timestamp_str,
                "message": message,
                "category": event.EventCategory,
                "record_number": event.RecordNumber,
                "data": event.Data if event.Data else ""
            }
        except Exception as e:
            return {
                "log": log_name,
                "error": f"Failed to parse event: {str(e)}"
            }
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """
        Parse timestamp string to datetime object
        
        Args:
            timestamp_str: Timestamp string from event
        
        Returns:
            datetime object
        """
        try:
            # Try ISO format first
            return datetime.fromisoformat(timestamp_str)
        except:
            try:
                # Try common Windows format
                return datetime.strptime(timestamp_str, "%m/%d/%Y %H:%M:%S")
            except:
                # Return current time as fallback
                return datetime.now()
    
    def get_statistics(self, events: List[Dict]) -> Dict:
        """
        Generate statistics from events
        
        Args:
            events: List of event dictionaries
        
        Returns:
            Dictionary with statistics
        """
        event_ids = {}
        event_types = {}
        
        for event in events:
            event_id = event.get("event_id")
            event_type = event.get("event_type")
            
            event_ids[event_id] = event_ids.get(event_id, 0) + 1
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        return {
            "total_events": len(events),
            "unique_event_ids": len(event_ids),
            "event_id_counts": event_ids,
            "event_type_counts": event_types,
            "top_events": sorted(event_ids.items(), key=lambda x: x[1], reverse=True)[:5]
        }


class EventFilter:
    """
    Filter and analyze events for security threats
    Day 16: Critical event filtering and threat detection
    """
    
    # Critical security event IDs
    CRITICAL_EVENT_IDS = {
        4624: {"name": "Successful Logon", "severity": "INFO"},
        4625: {"name": "Failed Logon", "severity": "WARNING"},
        4720: {"name": "User Account Created", "severity": "HIGH"},
        4726: {"name": "User Account Deleted", "severity": "HIGH"},
        4768: {"name": "Kerberos TGT Requested", "severity": "INFO"},
        4771: {"name": "Kerberos Pre-Auth Failed", "severity": "WARNING"},
        5140: {"name": "Network Share Accessed", "severity": "INFO"},
    }
    
    # Thresholds for anomaly detection
    THRESHOLDS = {
        "failed_logins_per_hour": 5,           # Alert if 5+ failed logins in 1 hour
        "failed_logins_per_day": 20,           # Alert if 20+ failed logins in 1 day
        "unusual_account_creation": 3,         # Alert if 3+ accounts created in 1 hour
        "unusual_account_deletion": 2,         # Alert if 2+ accounts deleted in 1 hour
    }
    
    def __init__(self):
        """Initialize event filter"""
        self.alerts = []
    
    def filter_critical(self, events: List[Dict]) -> List[Dict]:
        """
        Filter events to only include critical security events
        
        Args:
            events: List of event dictionaries
        
        Returns:
            Filtered list of critical events
        """
        critical_events = []
        
        for event in events:
            event_id = event.get("event_id")
            if event_id in self.CRITICAL_EVENT_IDS:
                # Add severity information
                event["severity"] = self.CRITICAL_EVENT_IDS[event_id]["severity"]
                event["event_name"] = self.CRITICAL_EVENT_IDS[event_id]["name"]
                critical_events.append(event)
        
        return critical_events
    
    def detect_brute_force(self, events: List[Dict], hours_back: int = 1) -> Dict:
        """
        Detect brute force attacks (multiple failed login attempts)
        
        Args:
            events: List of events to analyze
            hours_back: Time window in hours (default 1 hour)
        
        Returns:
            Dictionary with brute force analysis and alerts
        """
        analysis = {
            "detected": False,
            "total_failed_logins": 0,
            "by_user": {},
            "by_source": {},
            "alerts": []
        }
        
        # Count failed logins (Event ID 4625)
        for event in events:
            if event.get("event_id") == 4625:
                analysis["total_failed_logins"] += 1
                
                # Extract user if available
                user = event.get("message", "UNKNOWN").split("|")[0].strip()
                source = event.get("source", "UNKNOWN")
                
                analysis["by_user"][user] = analysis["by_user"].get(user, 0) + 1
                analysis["by_source"][source] = analysis["by_source"].get(source, 0) + 1
        
        # Check for brute force patterns
        if analysis["total_failed_logins"] >= self.THRESHOLDS["failed_logins_per_hour"]:
            analysis["detected"] = True
            analysis["alerts"].append({
                "severity": "HIGH",
                "type": "Brute Force Attack",
                "description": f"{analysis['total_failed_logins']} failed login attempts detected",
                "recommendation": "Investigate account access and review security logs"
            })
        
        # Check per-user brute force
        for user, count in analysis["by_user"].items():
            if count >= self.THRESHOLDS["failed_logins_per_hour"]:
                analysis["alerts"].append({
                    "severity": "HIGH",
                    "type": "User Brute Force",
                    "user": user,
                    "attempts": count,
                    "recommendation": f"Reset password for {user} and review access"
                })
        
        return analysis
    
    def detect_account_changes(self, events: List[Dict]) -> Dict:
        """
        Detect suspicious account creation/deletion patterns
        
        Args:
            events: List of events to analyze
        
        Returns:
            Dictionary with account change analysis
        """
        analysis = {
            "created_accounts": [],
            "deleted_accounts": [],
            "alerts": []
        }
        
        for event in events:
            event_id = event.get("event_id")
            
            # Account creation (Event 4720)
            if event_id == 4720:
                analysis["created_accounts"].append({
                    "timestamp": event.get("timestamp"),
                    "message": event.get("message", ""),
                    "event": event
                })
            
            # Account deletion (Event 4726)
            elif event_id == 4726:
                analysis["deleted_accounts"].append({
                    "timestamp": event.get("timestamp"),
                    "message": event.get("message", ""),
                    "event": event
                })
        
        # Check for unusual account creation patterns
        if len(analysis["created_accounts"]) >= self.THRESHOLDS["unusual_account_creation"]:
            analysis["alerts"].append({
                "severity": "HIGH",
                "type": "Unusual Account Creation",
                "count": len(analysis["created_accounts"]),
                "description": f"{len(analysis['created_accounts'])} accounts created - verify authorization",
                "recommendation": "Review all newly created accounts with security team"
            })
        
        # Check for unusual account deletion patterns
        if len(analysis["deleted_accounts"]) >= self.THRESHOLDS["unusual_account_deletion"]:
            analysis["alerts"].append({
                "severity": "MEDIUM",
                "type": "Unusual Account Deletion",
                "count": len(analysis["deleted_accounts"]),
                "description": f"{len(analysis['deleted_accounts'])} accounts deleted - verify authorization",
                "recommendation": "Review all deleted accounts with security team"
            })
        
        return analysis
    
    def detect_unusual_access(self, events: List[Dict]) -> Dict:
        """
        Detect unusual network access patterns
        
        Args:
            events: List of events to analyze
        
        Returns:
            Dictionary with unusual access analysis
        """
        analysis = {
            "network_shares_accessed": [],
            "after_hours_access": [],
            "alerts": []
        }
        
        for event in events:
            event_id = event.get("event_id")
            
            # Network share access (Event 5140)
            if event_id == 5140:
                analysis["network_shares_accessed"].append({
                    "timestamp": event.get("timestamp"),
                    "message": event.get("message", ""),
                    "event": event
                })
                
                # Check if access is outside business hours (22:00-06:00)
                try:
                    timestamp_str = event.get("timestamp", "")
                    # Parse hour from timestamp
                    if " " in timestamp_str:
                        time_part = timestamp_str.split(" ")[1]
                        hour = int(time_part.split(":")[0])
                        
                        if hour >= 22 or hour < 6:
                            analysis["after_hours_access"].append({
                                "timestamp": timestamp_str,
                                "hour": hour,
                                "message": event.get("message", "")
                            })
                except:
                    pass
        
        # Alert if suspicious access patterns
        if len(analysis["after_hours_access"]) > 0:
            analysis["alerts"].append({
                "severity": "MEDIUM",
                "type": "After-Hours Network Access",
                "count": len(analysis["after_hours_access"]),
                "description": f"{len(analysis['after_hours_access'])} network access attempts outside business hours",
                "recommendation": "Review after-hours network access logs"
            })
        
        return analysis
    
    def analyze_events(self, events: List[Dict]) -> Dict:
        """
        Comprehensive event analysis combining all detection methods
        
        Args:
            events: List of events to analyze
        
        Returns:
            Comprehensive analysis results
        """
        # Filter to critical events first
        critical_events = self.filter_critical(events)
        
        # Run all analysis methods
        brute_force = self.detect_brute_force(critical_events)
        account_changes = self.detect_account_changes(critical_events)
        unusual_access = self.detect_unusual_access(critical_events)
        
        # Compile results
        all_alerts = (brute_force["alerts"] + 
                     account_changes["alerts"] + 
                     unusual_access["alerts"])
        
        # Determine overall threat level
        threat_level = "LOW"
        if len(all_alerts) > 0:
            alert_severities = [a.get("severity") for a in all_alerts]
            if "CRITICAL" in alert_severities:
                threat_level = "CRITICAL"
            elif "HIGH" in alert_severities:
                threat_level = "HIGH"
            elif "MEDIUM" in alert_severities:
                threat_level = "MEDIUM"
        
        return {
            "timestamp": datetime.now().isoformat(),
            "events_analyzed": len(events),
            "critical_events_found": len(critical_events),
            "threat_level": threat_level,
            "brute_force_analysis": brute_force,
            "account_changes_analysis": account_changes,
            "unusual_access_analysis": unusual_access,
            "total_alerts": len(all_alerts),
            "alerts": all_alerts,
            "recommendations": self._compile_recommendations(all_alerts)
        }
    
    def _compile_recommendations(self, alerts: List[Dict]) -> List[str]:
        """
        Compile security recommendations based on alerts
        
        Args:
            alerts: List of alert dictionaries
        
        Returns:
            List of recommendations
        """
        recommendations = []
        
        for alert in alerts:
            rec = alert.get("recommendation")
            if rec and rec not in recommendations:
                recommendations.append(rec)
        
        return recommendations


# Installation Instructions
INSTALLATION_GUIDE = """
# Windows Event Log API Setup for SentinelAI

## Option 1: PyWin32 (Recommended for Windows Event Log access)

### Installation:
```bash
pip install pywin32
python -m pip install pywin32
pywin32_postinstall.py -install  # Run as administrator
```

### Privileges Required:
- Must run as Administrator
- Security log requires administrative account

### Key APIs:
- `win32evtlog.OpenEventLog(computer, logname)`
- `win32evtlog.ReadEventLog(handle, flags, recordOffset)`
- `win32evtlog.CloseEventLog(handle)`

### Usage Example:
```python
from sentinelai.event_logs import PyWin32Provider

provider = PyWin32Provider()
events = provider.read_logs("Security", 
                           filters={"event_ids": [4624, 4625, 4720]})
```

## Option 2: Windows Native Module (Alternative)

### Advantages:
- No external dependencies
- Built into Windows
- Native performance

### Implementation:
```python
import wmi  # Windows Management Instrumentation
```

## Critical Event IDs to Monitor

| Event ID | Name | Severity | Description |
|----------|------|----------|-------------|
| 4624 | Logon | INFO | Successful login |
| 4625 | Logon Failure | WARNING | Failed login attempt |
| 4720 | User Created | HIGH | New account created |
| 4726 | User Deleted | HIGH | Account deleted |
| 4768 | Kerberos TGT | INFO | Authentication ticket requested |
| 4771 | Kerberos Failure | WARNING | Kerberos auth failed |
| 5140 | Network Share | INFO | Network resource accessed |

## MITRE ATT&CK Mappings

- T1078: Valid Accounts (Event 4624)
- T1110: Brute Force (Events 4625, 4771)
- T1136: Create Account (Event 4720)
- T1531: Account Access Removal (Event 4726)
- T1558: Steal/Forge Kerberos Tickets (Events 4768, 4769)

## Week 3 Integration Plan

- Day 15: Set up pywin32 and test Security log access
- Day 16: Filter for critical event IDs
- Day 17: Build structured event log parser
- Day 18: Integrate `--logs` command into CLI
- Day 19: Connect to LLM analysis pipeline
"""


if __name__ == "__main__":
    print("Windows Event Log Research Module")
    print(f"PyWin32 Available: {PyWin32Provider().available}")
    
    # Show installation guide
    print(INSTALLATION_GUIDE)
    
    # Demonstrate with sample data
    print("\n" + "="*60)
    print("SAMPLE EVENT ANALYSIS")
    print("="*60)
    
    analyzer = EventLogAnalyzer()
    analysis = analyzer.analyze_security_events(SAMPLE_SECURITY_EVENTS)
    
    print(f"Events Analyzed: {analysis['events_analyzed']}")
    print(f"Threat Summary: {analysis['threat_summary']}")
    print(f"Critical Events: {len(analysis['critical_events'])}")
    print(f"Suspicious Patterns: {len(analysis['suspicious_patterns'])}")

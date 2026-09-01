# Day 15 Event Log LLM Analysis

Provider: ollama | Model: `gemma4:latest`

## 1. Executive Summary

This analysis covers the `CORP-HOSTS` security event log data collected over a 60-minute period. A total of nine distinct events need immediate attention, ranging from failed authentications to critical changes in system configuration. The single most important immediate action is to assume the integrity of the system has been compromised following the audit log clearing (Event ID 1102) and to contain the suspected threat actor's activities originating from `WORKSTATION-23` (10.0.5.23).

## 2. Prioritized Action List

### Finding #1 - Audit Log Clearance (Event ID 1102)
*   **Risk rating:** High — This event indicates that an attacker or privileged insider was actively attempting to cover their tracks by clearing system evidence.
*   **Verify now:** 1. Confirm current Windows Event Log retention policies (e.g., using `wevtutil` or Group Policy). 2. Check the system event log/security log for preceding successful logons or unusual process execution details leading up to the 1102 event.
*   **Fix:** Implement strict log protection mechanisms. Configure advanced audit policies to monitor for log clearing attempts. Ensure critical system logs are streamed or backed up off-host to a Security Information and Event Management (SIEM) system to prevent local tampering. Reference "CIS Windows Benchmark" controls for log management.
*   **Reference:** Event ID 1102 (Critical)

### Finding #2 - Unauthorized User Account Creation (Event ID 4720)
*   **Risk rating:** High — Creating new accounts, especially without a clear business justification, is a classic persistence or lateral movement technique.
*   **Verify now:** 1. Identify the specific user account created (if available in the full log details) and check its current group memberships and permissions. 2. Perform a group membership audit on privileged groups (e.g., Domain Admins, Enterprise Admins) to ensure no unapproved accounts were added.
*   **Fix:** Enforce robust change control and strict permissions for account management. Implement Privileged Access Management (PAM) solutions to require just-in-time (JIT) elevation and dedicated approval workflows for all account creations and modification.
*   **Reference:** Event ID 4720, Source Host: `WORKSTATION-23`

### Finding #3 - Failed Logon Attempts (Event ID 4625)
*   **Risk rating:** Medium — Multiple failed logon attempts against the `svc_web` account (Network Logon Type 3) suggest either a brute-force attack or a credential misconfiguration issue.
*   **Verify now:** 1. Check the source IP `10.0.5.23` (WORKSTATION-23) to determine if the source host is authorized for service account network access. 2. Review the account lockout policy settings for the `svc_web` account.
*   **Fix:** Implement mandatory Multi-Factor Authentication (MFA) for all service accounts accessing the network. Configure strict account lockout policies (e.g., 3 failed attempts within 15 minutes) and limit the source IPs allowed to authenticate to `svc_web` using Network Access Control (NAC) or firewall rules.
*   **Reference:** Event ID 4625, Account: `svc_web`, Source IP: `10.0.5.23`

### Finding #4 - Privilege Elevation and RunAs Use (Event IDs 4648, 4672)
*   **Risk rating:** Medium — The sequence of running as `devops` using explicit credentials (4648) followed by the assignment of special privileges (4672) indicates a possible escalation path that must be verified.
*   **Verify now:** 1. Audit the specific security policies applied when the `devops` account was logged on. 2. Confirm if the combination of explicit credentials used via `RunAs` (4648) was required for the task performed.
*   **Fix:** Enforce the Principle of Least Privilege (PoLP). Limit the ability of users to use explicit credentials for elevated sessions unless absolutely necessary, and ensure that temporary elevated privileges are automatically revoked upon session termination.
*   **Reference:** Event IDs 4648, 4672, Account: `devops`

### Finding #5 - Unauthorized Account Activity/Scope Check (Event IDs 5145, 4663)
*   **Risk rating:** Low — These events document the successful, but potentially broad, scope of access achieved by the `devops` account to network resources. They confirm the need to restrict the account's blast radius.
*   **Verify now:** 1. Audit the group memberships for the `devops` account and remove any permissions that grant access beyond its required operational scope (e.g., if it only needs read access, ensure it does not have write access). 2. Review network share access control lists (ACLs) related to objects accessed by `devops`.
*   **Fix:** Implement granular Access Control Lists (ACLs) on all sensitive network shares and objects. Use dedicated service accounts for service functions rather than allowing development or primary operational accounts (`devops`) to hold excessive privileges.
*   **Reference:** Event IDs 5145, 4663, Account: `devops`

## 3. Compliance Cross-Check

| Event ID | Description | Relevant Framework Control |
| :--- | :--- | :--- |
| 1102 | Audit log clearing | Auditing and Monitoring (System Integrity / Retention) |
| 4720 | User account creation | Change Management & Least Privilege (User Lifecycle Management) |
| 4625 | Failed logon attempts | Authentication Controls (Password Strength / MFA / Account Lockout) |
| 4648, 4672 | Privilege elevation / RunAs | Privileged Access Management (PoLP / JIT Access) |
| 5145, 4663 | Object/Share Access | Least Privilege (Network Segmentation / ACL Enforcement) |

## 4. Verification Plan

After applying the remediation steps, use the following checklist to confirm controls are restored and working correctly:

1.  **Audit Log Integrity:** Attempt to clear the event logs locally and confirm that the system alerts (via SIEM or local policy) and records the action (re-check for new 1102 events).
2.  **Account Lockout Policy:** Force a failure scenario for the `svc_web` account to verify that the defined lockout policy (e.g., 3 attempts) is active and correctly triggered.
3.  **Account Creation Controls:** Attempt to create a new user account using the elevated account credentials and confirm that the attempt is blocked or requires mandatory JIT approval.
4.  **Least Privilege Review:** Run a report to list the current group memberships for the `devops` account and confirm that the list matches the minimal required operational role.
5.  **Audit Monitoring:** Review the Security Event Log in the SIEM/Log collector to ensure that both account creations (4720) and log clearing attempts (1102) are triggering high-priority alerts.

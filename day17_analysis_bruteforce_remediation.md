# Day 17 Event Log Remediation - bruteforce

Provider: ollama | Model: `gemma4:latest`

## 1. Executive Summary

This remediation plan covers the Windows Security Event Log data collected from the **SRV-DC01** host, analyzing 4 distinct security event types across multiple accounts. The single most important immediate action is to **restrict or block the source IP address 203.0.113.77** and verify the current security posture of the `Administrator` and `svc_oracle` accounts, which were subjected to brute-force logon attempts.

## 2. Prioritized Action List

**Finding #1 - Multiple Failed Logon Attempts (Event ID 4625)**
- **Risk rating:** High — These repeated failures against critical domain accounts (`Administrator`, `admin`, `svc_oracle`) strongly indicate unauthorized brute-force attempts or account enumeration.
- **Verify now:** 1. Review the domain security policy for account lockout thresholds and duration. 2. Filter the event log for all subsequent 4625 events involving the source IP `203.0.113.77` to confirm if the activity stopped after the observed time window.
- **Fix:** 1. Implement strict Account Lockout Policies (e.g., maximum 5 failed attempts, 30-minute lockout) to automatically mitigate brute-force attacks (CIS Windows Benchmark). 2. For high-value accounts (e.g., `Administrator`), require Multi-Factor Authentication (MFA) for remote interactive logons (NIST 800-63B). 3. If source IP `203.0.113.77` is not a trusted source, block it at the firewall level.
- **Reference:** Event ID 4625 (multiple instances), Accounts: Administrator, admin, svc_oracle.

**Finding #2 - Successful Logon using Dedicated Service Account (Event IDs 4624, 4672, 4648)**
- **Risk rating:** Medium — A high-privilege account (`backupadmin`) was successfully used for a remote interactive logon, requiring immediate investigation into *why* this account was used from an unidentified source.
- **Verify now:** 1. Determine the legitimate business function and geographic location for the `backupadmin` account. 2. Audit the policy governing the privileges assigned to `backupadmin` to ensure least privilege is maintained.
- **Fix:** 1. Implement principle of least privilege (PoLP); restrict the permissions granted to `backupadmin` only to the necessary resources. 2. If this account is only for backup purposes, enforce that logins must originate only from authorized, segmented network IPs (e.g., dedicated backup subnet). 3. Consider rotating the credentials for the `backupadmin` account immediately.
- **Reference:** Event ID 4624, 4672, 4648. Account: backupadmin.

**Finding #3 - Account Locked Out (Event ID 4740)**
- **Risk rating:** Medium — While this event records the *result* of the failed logins, it confirms that the account lockout policy was triggered, which is good defense but requires policy review.
- **Verify now:** 1. Confirm that the lockout duration and failure count policies align with the organization's risk tolerance. 2. Check if other high-value accounts besides `Administrator` are configured with similar policies.
- **Fix:** Ensure that account lockout mechanisms are configured and enforced across all sensitive domain accounts. If the lockout period is too short, an attacker might cycle through accounts quickly; ensure the duration is sufficient to deter automated attacks.
- **Reference:** Event ID 4740. Account: Administrator.

**Finding #4 - Evidence of Explicit Credential Usage (Event ID 4648)**
- **Risk rating:** Low — This event confirms the technical method used by the successful `backupadmin` logon, providing crucial context for the investigation (Finding #2).
- **Verify now:** 1. Analyze other successful logon events (4624) from the source IP `203.0.113.77` to see if explicit credentials were used across multiple accounts. 2. Confirm if the successful use of explicit credentials requires additional logging or monitoring triggers.
- **Fix:** N/A - This is purely an informative event that guides the hardening efforts outlined in Finding #2.

## 3. Compliance Cross-Check

**Finding #1 - Multiple Failed Logon Attempts (Event ID 4625):** Account Lockout / Authentication Strength (e.g., NIST 800-63B)
**Finding #2 - Successful Logon using Dedicated Service Account (Event IDs 4624, 4672, 4648):** Least Privilege / Privileged Account Management (CIS Windows Benchmark)
**Finding #3 - Account Locked Out (Event ID 4740):** Access Control Enforcement / Authentication Policies (NIST 800-63B)
**Finding #4 - Evidence of Explicit Credential Usage (Event ID 4648):** Auditing/Monitoring Capabilities (Auditing/Log Retention)

## 4. Verification Plan

Upon completing the remediation steps, perform the following checks:

*   **Brute Force Prevention:** Attempt to log into a restricted domain account using the source IP `203.0.113.77` (or a local test account). Verify that the account locks out successfully after the configured number of failed attempts (Verifies Finding #1 and #3 fixes).
*   **Privilege Check:** Audit the `backupadmin` account group memberships and policies to confirm that access is limited only to necessary resources (Verifies Finding #2 fixes).
*   **Network Control:** Test the perimeter firewall rules to ensure that the source IP `203.0.113.77` is correctly blocked or restricted from reaching the DC network (Verifies Finding #1 fixes).
*   **Logging Check:** Confirm that successful and failed logon attempts are still being logged at the necessary verbosity, and that Event ID 1102 (Audit Log Cleared) has not occurred since the initial collection window.

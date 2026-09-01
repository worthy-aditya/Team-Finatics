# Day 17 Event Log Remediation - bruteforce

Provider: gemini | Model: `gemini-3.6-flash`

## 1. Executive Summary
This remediation plan addresses activity recorded on host `SRV-DC01`, where 30 event instances across 7 distinct log entries indicate a brute-force / password-spraying campaign originating from external IP `203.0.113.77` via Remote Desktop (Logon Type 10). The attack targeted multiple accounts (`Administrator`, `admin`, `svc_oracle`), resulting in an account lockout for `Administrator` and a successful compromised logon for `backupadmin` with elevated privileges. The single most critical immediate action is to isolate host `SRV-DC01` from source IP `203.0.113.77`, disable the compromised `backupadmin` account, terminate its active RDP sessions, and reset its credentials.

---

## 2. Prioritized Action List

### Finding #1 - Successful Privileged RDP Logon (Event ID 4624 & Event ID 4672)
* **Risk rating:** High — A remote interactive logon succeeded from an external, untrusted IP (`203.0.113.77`) using `backupadmin` and was immediately assigned high-privilege user rights.
* **Verify now:** Run `Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4624} | Where-Object {$_.Properties[18].Value -eq '203.0.113.77'}` and `Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4672}` to confirm session duration, assigned privileges, and active logons for `backupadmin`.
* **Fix:** Disable the `backupadmin` account immediately and revoke active user sessions. Block RDP access at the perimeter firewall from IP `203.0.113.77`. Enforce Network Level Authentication (NLA) and require Multi-Factor Authentication (MFA) for all RDP access in accordance with CIS Windows Server Benchmark guidelines.
* **Reference:** Event IDs 4624, 4672; Source IP: `203.0.113.77`; Account: `backupadmin`.

---

### Finding #2 - Explicit Credential Usage Attempt (Event ID 4648)
* **Risk rating:** High — The compromised account `backupadmin` attempted to run a process or access resources using explicit secondary credentials from source IP `203.0.113.77`.
* **Verify now:** Execute `Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4648}` to identify the target domain/account and process name spawned during the explicit credential logon attempt by `backupadmin`.
* **Fix:** Terminate all rogue processes spawned by `backupadmin`, perform forensic analysis on targeted secondary accounts, and restrict credential delegation and secondary logon capabilities per NIST SP 800-63B standards.
* **Reference:** Event ID 4648; Source IP: `203.0.113.77`; Account: `backupadmin`.

---

### Finding #3 - User Account Lockout (Event ID 4740)
* **Risk rating:** Medium — Automated login attempts triggered account lockout thresholds on the built-in `Administrator` account, causing temporary denial of access.
* **Verify now:** Execute `Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4740}` to confirm the exact lockout timestamp and verify that no unauthorized unlocking attempts occurred.
* **Fix:** Ensure built-in `Administrator` account is renamed or restricted from remote interactive (Logon Type 10) logons. Maintain robust account lockout policies aligned with CIS Security Benchmarks.
* **Reference:** Event ID 4740; Account: `Administrator`.

---

### Finding #4 - Multiple Remote Interactive Failed Logons (Event ID 4625)
* **Risk rating:** Medium — High volume of failed RDP authentication attempts from IP `203.0.113.77` targeting multiple accounts (`Administrator`, `admin`, `svc_oracle`).
* **Verify now:** Run `Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4625} | Where-Object {$_.Properties[19].Value -eq '203.0.113.77'}` to confirm total failed attempts and check for additional targeted usernames.
* **Fix:** Block IP `203.0.113.77` at the edge firewall, restrict RDP exposure to internal VPN segments only, and disable default/service accounts (`svc_oracle`) from interactive remote logon rights per NIST SP 800-53 AC-7 (Unsuccessful Logon Attempts).
* **Reference:** Event ID 4625; Source IP: `203.0.113.77`; Accounts: `Administrator`, `admin`, `svc_oracle`.

---

## 3. Compliance Cross-Check

* **Finding #1 (Event IDs 4624 / 4672):** Maps to **NIST SP 800-53 AC-2 (Account Management)** and **AC-6 (Least Privilege)** for managing privileged remote sessions.
* **Finding #2 (Event ID 4648):** Maps to **NIST SP 800-53 IA-2 (Identification and Authentication)** regarding secondary explicit credential use.
* **Finding #3 (Event ID 4740):** Maps to **NIST SP 800-53 AC-7 (Unsuccessful Logon Attempts)** for automated enforcement of lockout thresholds.
* **Finding #4 (Event ID 4625):** Maps to **CIS Control 4.3 (Configure Automatic Account Locking)** and **NIST SP 800-53 AC-7** for monitoring and mitigating brute-force attacks.

---

## 4. Verification Plan

- [ ] **Account State Check:** Confirm that account `backupadmin` is disabled and all existing Remote Desktop sessions on `SRV-DC01` associated with it are terminated.
- [ ] **Log Monitoring (Event ID 4625):** Re-query `Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4625}` to verify no new failed logon attempts are occurring from IP `203.0.113.77`.
- [ ] **Privilege Audit (Event ID 4672):** Run `Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4672}` to confirm no unexplained privilege assignments are occurring.
- [ ] **Account Status Check (Event ID 4740):** Verify `Administrator` account status and ensure proper lockout controls remain active.
- [ ] **Firewall Rule Verification:** Inspect perimeter firewall logs to confirm that all incoming traffic from `203.0.113.77` to port 3389 (RDP) on `SRV-DC01` is actively dropped.

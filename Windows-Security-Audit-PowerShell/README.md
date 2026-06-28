# Windows Security Audit Script

A PowerShell-based security audit script for Windows systems. Designed to help administrators quickly assess the security posture of a machine by checking firewall configuration, password policies, running services, installed applications, and common hardening benchmarks.

> **Status:** Active development — Firewall and Password Policy sections complete. Service, App, and Hardening checks in progress.

---

## Why I Built This

Manual security audits are time-consuming and easy to miss some steps. The intention behind this security audit is to make windows security checks automatic before starting any important work. Ensuring that a windows system is secure, should be first priority to ensure sensitive data is protected. This script is a demonstration of the skills I learned in my Cybersecurity class, and how I would apply them to a real life situation.

---

## What It Checks

| Section | Status | Description |
|---|---|---|
| Firewall Audit | ✅ Complete | Verifies Domain, Private, and Public profiles are enabled |
| Password Policy Audit | ✅ Complete | Checks length, age, complexity, lockout, and history settings |
| Service Audit | 🔧 In Progress | Enumerates running services and diffs against a saved baseline |
| Authorized Apps (Winget) | 🔧 In Progress | Lists installed apps and flags anything not on an approved list |
| Hardening Checks | 🔧 In Progress | BitLocker, RDP, SSH, audit logging, and more |

---

## Requirements

- Windows 10 or Windows 11 / Windows Server 2016 or later
- PowerShell 5.1 or later
- Must be run as **Administrator**
- Winget installed (for Section 4 only)

---

## Usage

```powershell
# Clone the repo
git clone https://github.com/yourusername/windows-security-audit.git

# Open an elevated PowerShell session, then run:
.\WindowsSecurityAudit.ps1
```

All output is saved to `C:\AuditResults\` by default. Each run creates a new timestamped folder so results are never overwritten.

---

## Output Files

Every run produces the following files under `C:\AuditResults\`:

```md
AuditLog_20240615_143022.txt              # Full running log of the audit session
FirewallReport_20240615_143022.txt        # Human-readable firewall PASS/FAIL summary
Firewall_20240615_143022.csv              # Full firewall rule export
PasswordPolicyReport_20240615_143022.txt  # Password policy findings
PasswordPolicy_20240615_143022.csv        # Structured policy values with PASS/FAIL
Services_20240615_143022.csv             # Full service snapshot
ServicesBaseline_20240615_143022.csv     # Saved baseline for future comparison
WingetInstalled_20240615_143022.csv      # Installed apps with authorization status
HardeningChecks_20240615_143022.csv      # Hardening check results
AuditSummary_20240615_143022.txt         # Consolidated findings across all sections
```

---

## Configuration

All file paths and output locations are controlled by global variables at the top of the script — nothing is hardcoded inside the functions. To change the output directory or point to an existing baseline, edit this block:

```powershell
$Global:AuditOutputDir         = "C:\AuditResults"
$Global:ServicesPreviousBaseline = ""   # Point to a prior baseline CSV to enable diffing
$Global:WingetApprovedAppsFile   = ""   # Path to approved app ID list for policy check
```

---

## Roadmap

- [x] Script structure and global variable block
- [x] Helper functions (Write-Log, Initialize-AuditEnvironment)
- [x] Section 1 — Firewall Audit
- [x] Section 2 — Password Policy Audit
- [ ] Section 3 — Service Audit with baseline diff
- [ ] Section 4 — Authorized App Policy via Winget
- [ ] Section 5a — Windows Update status
- [ ] Section 5b — Defender / AV status
- [ ] Section 5c — BitLocker check
- [ ] Section 5d — RDP / NLA check
- [ ] Section 5e — SMBv1 disabled check
- [ ] Section 5f — Local admin account review
- [ ] Section 5g — Guest account check
- [ ] Section 5h — UAC configuration
- [ ] Section 5i — Audit policy / event logging
- [ ] Section 5j — PowerShell script block logging
- [ ] Section 5k — Scheduled task review
- [ ] Section 5l — Open network shares
- [ ] Section 5m — AutoPlay / AutoRun disabled
- [ ] Final summary report aggregation

---

## Skills Demonstrated

- PowerShell scripting and function design
- Windows security concepts (firewall profiles, password policy, SSH and RDP checks)
- Structured logging and CSV export for audit trails
- Baseline comparison pattern for change detection
- Script scope management and modular design

---

## License

MIT

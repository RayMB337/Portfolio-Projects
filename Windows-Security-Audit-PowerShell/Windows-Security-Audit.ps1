#Requires -RunAsAdministrator
<#
===============================================================================
  WINDOWS SECURITY AUDIT SCRIPT
  Description : Windows audit Script covering Firewall, Password Policy,
                Services, Authorized Apps (Winget), and additional hardening
                checks. 
  Author      : Raymundo Barrera
  Version     : 1.0
  Last Updated: 06/28/2026
  
  USAGE:
    Run from an elevated PowerShell session:
    .\WindowsSecurityAudit.ps1

  NOTE: All output paths are controlled via the Global Variables section below.
        Adjust them before running.
===============================================================================
#>

# ============================================================
#  GLOBAL VARIABLES — Adjust paths and names here only.
#  All sections reference these variables; do not hardcode
#  paths inside individual sections.
# ============================================================

# --- Output Directory ---
# Root folder where all audit results will be saved.
$Global:AuditOutputDir = "C:\AuditResults"

# --- Audit Session Timestamp ---
# Appended to every output file so runs never overwrite each other.
$Global:AuditTimestamp = (Get-Date -Format "yyyyMMdd_HHmmss")

# --- Main Log File ---
# Running log of every action and finding during the audit.
$Global:LogFile = "$Global:AuditOutputDir\AuditLog_$Global:AuditTimestamp.txt"

# --- Section: Firewall Audit ---
$Global:FirewallCsvExport = "$Global:AuditOutputDir\Firewall_$Global:AuditTimestamp.csv"
$Global:FirewallReportFile = "$Global:AuditOutputDir\FirewallReport_$Global:AuditTimestamp.txt"

# --- Section: Password Policy Audit ---
$Global:PasswordPolicyCsvExport = "$Global:AuditOutputDir\PasswordPolicy_$Global:AuditTimestamp.csv"
$Global:PasswordPolicyReportFile = "$Global:AuditOutputDir\PasswordPolicyReport_$Global:AuditTimestamp.txt"

# --- Section: Service Policy Audit ---
$Global:ServicesCsvExport = "$Global:AuditOutputDir\Services_$Global:AuditTimestamp.csv"
$Global:ServicesBaselineFile = "$Global:AuditOutputDir\ServicesBaseline_$Global:AuditTimestamp.csv"
# Path to a previously saved baseline for comparison (leave empty to skip diff).
$Global:ServicesPreviousBaseline = ""  # e.g. "C:\AuditResults\ServicesBaseline_20240101_120000.csv"

# --- Section: Authorized App Policy (Winget) ---
$Global:WingetInstalledCsvExport = "$Global:AuditOutputDir\WingetInstalled_$Global:AuditTimestamp.csv"
$Global:WingetBaselineFile = "$Global:AuditOutputDir\WingetBaseline_$Global:AuditTimestamp.csv"
# Path to an approved-apps list (one App ID per line) for policy comparison.
$Global:WingetApprovedAppsFile = ""  # e.g. "C:\Policies\ApprovedApps.txt"


# --- Final Summary Report ---
$Global:SummaryReportFile = "$Global:AuditOutputDir\AuditSummary_$Global:AuditTimestamp.txt"


# ============================================================
#  HELPER FUNCTIONS
#  Utility functions used by every section below.
# ============================================================

function Write-Log {
    <#
    .SYNOPSIS
        Writes a timestamped entry to the main log file and console.
    .PARAMETER Message
        The text to log.
    .PARAMETER Level
        INFO | WARN | ERROR
    #>
    param(
        [string]$Message,
        [ValidateSet("INFO", "WARN", "ERROR")]
        [string]$Level = "INFO"
    )
    $entry = "[{0}] [{1}] {2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Level, $Message
    Add-Content -Path $Global:LogFile -Value $entry
    switch ($Level) {
        "WARN" { Write-Host $entry -ForegroundColor Yellow }
        "ERROR" { Write-Host $entry -ForegroundColor Red }
        default { Write-Host $entry }
    }
}

function Initialize-AuditEnvironment {
    <#
    .SYNOPSIS
        Creates the output directory and writes the audit header to the log.
    #>
    if (-not (Test-Path $Global:AuditOutputDir)) {
        New-Item -ItemType Directory -Path $Global:AuditOutputDir -Force | Out-Null
    }
    Write-Log "============================================================"
    Write-Log "  Windows Security Audit Started"
    Write-Log "  Host     : $env:COMPUTERNAME"
    Write-Log "  User     : $env:USERNAME"
    Write-Log "  Output   : $Global:AuditOutputDir"
    Write-Log "============================================================"
}

 
 
# ============================================================
#  SECTION 1 — FIREWALL AUDIT
#  Goal: Confirm Windows Defender Firewall is ENABLED on all
#        three profiles (Domain, Private, Public) and export
#        the active ruleset for review.
# ============================================================
 
function Invoke-FirewallAudit {
    Write-Log "--- BEGIN: Firewall Audit ---"
 
    # ---------------------------------------------------------------
    # STEP 1 — Collect data
    #   Get all three firewall profiles (Domain, Private, Public).
    #   Each object has a Name and Enabled property.
    # ---------------------------------------------------------------
    
    try {
        $profiles = Get-NetFirewallProfile | Select-Object Name, Enabled
 
        # ---------------------------------------------------------------
        # STEP 2 — Evaluate findings
        #   Loop through each profile and build a result object.
        #   We store results in an array so we can export and report later.
        #   $null = @() creates an empty array to collect into.
        # ---------------------------------------------------------------
        $firewallResults = @()
 
        foreach ($p in $profiles) {
 
            if ($p.Enabled -eq $true) {
                $status = "PASS"
                Write-Log "Firewall profile '$($p.Name)' is ENABLED - PASS"
            }
            else {
                $status = "FAIL"
                Write-Log "Firewall profile '$($p.Name)' is DISABLED - FAIL" -Level "WARN"
            }
 
            # Build a clean result object for this profile.
            # [PSCustomObject] lets us define exactly which columns we want.
            $firewallResults += [PSCustomObject]@{
                Profile = $p.Name
                Enabled = $p.Enabled
                Status  = $status
            }
        }
 
        # ---------------------------------------------------------------
        # STEP 3 — Export active firewall rules to CSV
        #   We only export enabled rules to keep the file readable.
        #   Select-Object trims it down to the columns that matter.
        # ---------------------------------------------------------------
        Write-Log "Exporting active firewall rules to: $Global:FirewallCsvExport"
 
        Get-NetFirewallRule | Where-Object { $_.Enabled -eq 'True' } |
        Select-Object DisplayName, Enabled, Profile, Direction, Action, DisplayGroup |
        Export-Csv -Path $Global:FirewallCsvExport -NoTypeInformation
 
        Write-Log "Firewall rules exported successfully."
 
        # ---------------------------------------------------------------
        # STEP 4 — Write human-readable report to FirewallReportFile
        #   Add-Content appends a line to the report file.
        #   This file is meant to be read by a person, not parsed by code.
        # ---------------------------------------------------------------
        $passCount = ($firewallResults | Where-Object { $_.Status -eq "PASS" }).Count
        $failCount = ($firewallResults | Where-Object { $_.Status -eq "FAIL" }).Count
 
        $reportLines = @(
            "============================================================",
            "  FIREWALL AUDIT REPORT",
            "  Host      : $env:COMPUTERNAME",
            "  Timestamp : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
            "============================================================",
            "",
            "PROFILE STATUS",
            "--------------"
        )
 
        foreach ($r in $firewallResults) {
            $reportLines += "  [$($r.Status)] $($r.Profile) Profile — Enabled: $($r.Enabled)"
        }
 
        $reportLines += ""
        $reportLines += "SUMMARY: $passCount PASS / $failCount FAIL"
        $reportLines += ""
        $reportLines += "Active rules exported to:"
        $reportLines += "  $Global:FirewallCsvExport"
        $reportLines += "============================================================"
 
        # Write all lines to the report file at once
        $reportLines | Set-Content -Path $Global:FirewallReportFile
 
        Write-Log "Firewall report written to: $Global:FirewallReportFile"
        Write-Log "Firewall Audit complete — $passCount PASS / $failCount FAIL"
        Write-Log "--- END: Firewall Audit ---"
    }
    catch {
        Write-Host -Object "[ERROR] Unable to get Firewall Status; Run as Administrator"
        Write-Host -Object "[ERROR] $($_.Exception.Message)"
    }
    
}


# ============================================================
#  SECTION 2 — PASSWORD POLICY AUDIT
#  Goal: Extract and evaluate all Windows password and account
#        lockout policies against your security baseline.
# ============================================================

function Invoke-PasswordPolicyAudit {
    Write-Log "--- BEGIN: Password Policy Audit ---"
 
    try {
        # ---------------------------------------------------------------
        # STEP 1 — Define expected baseline values
        # ---------------------------------------------------------------
        $expectedPolicy = @{
            MinimumPasswordLength = 12
            MinimumPasswordAge    = 1
            MaximumPasswordAge    = 90
            PasswordHistorySize   = 24
            PasswordComplexity    = 1   # 1 = Enabled, 0 = Disabled
            ClearTextPassword     = 0   # 0 = Disabled (reversible encryption OFF)
            LockoutBadCount       = 5   # 0 = never lockout, anything else = threshold
            LockoutDuration       = 15  # minutes
            ResetLockoutCount     = 15  # minutes
        }
 
        # ---------------------------------------------------------------
        # STEP 2 — Export local security policy to a temp file via secedit
        # ---------------------------------------------------------------
        $tempSecCfg = "$env:TEMP\secpol_audit.cfg"
 
        Write-Log "Exporting local security policy via secedit..."
 
        secedit /export /cfg $tempSecCfg /quiet
 
        # ---------------------------------------------------------------
        # STEP 3 — Parse the cfg file into a hashtable
        #   Each line in the file looks like: MinimumPasswordLength = 7
        #   We split on ' = ' and store key/value pairs in $seceditValues.
        # ---------------------------------------------------------------
        $seceditValues = @{}
 
        Get-Content $tempSecCfg | ForEach-Object {
            if ($_ -match '^\s*(.+?)\s*=\s*(.+)$') {
                $seceditValues[$Matches[1].Trim()] = $Matches[2].Trim()
            }
        }
 
        # Clean up the temp file now that values are in memory
        Remove-Item $tempSecCfg -Force
        Write-Log "Temp policy file removed."
 
        # ---------------------------------------------------------------
        # STEP 4 — Extract and cast each value to an integer
        #   MaximumPasswordAge is stored as a negative number by secedit,
        #   so we wrap it in [Math]::Abs() to get the positive value.
        # ---------------------------------------------------------------
        $actualMinLength = [int]$seceditValues["MinimumPasswordLength"]
        $actualMinAge = [int]$seceditValues["MinimumPasswordAge"]
        $actualMaxAge = [Math]::Abs([int]$seceditValues["MaximumPasswordAge"])
        $actualHistorySize = [int]$seceditValues["PasswordHistorySize"]
        $actualComplexity = [int]$seceditValues["PasswordComplexity"]
        $actualClearText = [int]$seceditValues["ClearTextPassword"]
        $actualLockoutCount = [int]$seceditValues["LockoutBadCount"]
        $actualLockoutDuration = [int]$seceditValues["LockoutDuration"]
        $actualResetLockout = [int]$seceditValues["ResetLockoutCount"]
 
        # TSTEP 5 — Evaluate each value against $expectedPolicy.
        #       Build a $policyResults array of [PSCustomObject] rows,
        #       one per policy setting, each with PASS or FAIL status.
        #       Follow the same pattern used in Invoke-FirewallAudit.
        $policyChecks = @(
            #  Policy name                Actual value            Expected value                              Operator
            @{ Policy = "MinimumPasswordLength"; Actual = $actualMinLength; Expected = $expectedPolicy["MinimumPasswordLength"]; Operator = "ge" },
            @{ Policy = "MinimumPasswordAge"; Actual = $actualMinAge; Expected = $expectedPolicy["MinimumPasswordAge"]; Operator = "ge" },
            @{ Policy = "MaximumPasswordAge"; Actual = $actualMaxAge; Expected = $expectedPolicy["MaximumPasswordAge"]; Operator = "le" },
            @{ Policy = "PasswordHistorySize"; Actual = $actualHistorySize; Expected = $expectedPolicy["PasswordHistorySize"]; Operator = "ge" },
            @{ Policy = "PasswordComplexity"; Actual = $actualComplexity; Expected = $expectedPolicy["PasswordComplexity"]; Operator = "eq" },
            @{ Policy = "ClearTextPassword"; Actual = $actualClearText; Expected = $expectedPolicy["ClearTextPassword"]; Operator = "eq" },
            @{ Policy = "LockoutBadCount"; Actual = $actualLockoutCount; Expected = $expectedPolicy["LockoutBadCount"]; Operator = "le" },
            @{ Policy = "LockoutDuration"; Actual = $actualLockoutDuration; Expected = $expectedPolicy["LockoutDuration"]; Operator = "ge" },
            @{ Policy = "ResetLockoutCount"; Actual = $actualResetLockout; Expected = $expectedPolicy["ResetLockoutCount"]; Operator = "ge" }
        )

        $policyResults = @()

        foreach ($check in $policyChecks) {
            $pass = switch ($check.Operator) {
                "ge" { $check.Actual -ge $check.Expected }
                "le" { $check.Actual -le $check.Expected }
                "eq" { $check.Actual -eq $check.Expected }
            }

            $status = if ($pass) { "PASS" } else { "FAIL" }

            Write-Log "$($check.Policy) — Expected: $($check.Expected) | Actual: $($check.Actual) | $status"

            $policyResults += [PSCustomObject]@{
                Policy   = $check.Policy
                Expected = $check.Expected
                Actual   = $check.Actual
                Status   = $status
            }
        }

 
        # STEP 6 — Export $policyResults to $Global:PasswordPolicyCsvExport.
        Write-Log "Exporting password policies to: $Global:PasswordPolicyCsvExport"    
        $policyResults | Export-Csv -Path $Global:PasswordPolicyCsvExport -NoTypeInformation
        Write-Log "Password policy exported successfully."

        # STEP 7 — Write human-readable summary to $Global:PasswordPolicyReportFile.
        $passCount = ($policyResults | Where-Object { $_.Status -eq "PASS" }).Count
        $failCount = ($policyResults | Where-Object { $_.Status -eq "FAIL" }).Count
 
        $reportLines = @(
            "============================================================",
            "  Password Policy AUDIT REPORT",
            "  Host      : $env:COMPUTERNAME",
            "  Timestamp : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
            "============================================================",
            "",
            "POLICY STATUS",
            "-------------"
        )
 
        foreach ($r in $policyResults) {
            $reportLines += "  [$($r.Status)] $($r.Policy) — Expected: $($r.Expected) | Actual: $($r.Actual)"
        }
 
        $reportLines += ""
        $reportLines += "SUMMARY: $passCount PASS / $failCount FAIL"
        $reportLines += ""
        $reportLines += "Password Policy Rules Exported to:"
        $reportLines += "  $Global:PasswordPolicyCsvExport"
        $reportLines += "============================================================"
 
        # Write all lines to the report file at once
        $reportLines | Set-Content -Path $Global:PasswordPolicyReportFile
 
        Write-Log "Password policy report written to: $Global:PasswordPolicyReportFile"
        Write-Log "Password policy Audit complete — $passCount PASS / $failCount FAIL"
        Write-Log "--- END: Password Policy Audit ---"
 
    }
    catch {
        Write-Log "Failed to complete Password Policy Audit: $($_.Exception.Message)" -Level "ERROR"
    }
 
    Write-Log "--- END: Password Policy Audit ---"
}

# ============================================================
#  SECTION 3 — SERVICE POLICY AUDIT
#  Goal: Enumerate all running services, flag unexpected or
#        high-risk entries, and produce / compare a baseline.
# ============================================================

function Invoke-ServiceAudit {
    Write-Log "--- BEGIN: Service Policy Audit ---"

    # TODO: Collect all services (running and stopped) with Name, DisplayName,
    #       Status, StartType, and the account they run under.
    #       Example cmdlet: Get-Service | Select-Object ...
    #                   or: Get-WmiObject Win32_Service
    #
    # TODO: Flag services running as LocalSystem / SYSTEM that are not
    #       expected, or any service running as a named admin account.
    #
    # TODO: Save the current snapshot to $Global:ServicesBaselineFile so it
    #       can be used as the previous baseline on the next run.
    #
    # TODO: If $Global:ServicesPreviousBaseline is set, import it and diff
    #       against the current snapshot. Report new, removed, or changed
    #       services (StartType or RunAs changes are especially important).
    #
    # TODO: Export full service list to $Global:ServicesCsvExport.

    Write-Log "--- END: Service Policy Audit ---"
}


# ============================================================
#  SECTION 4 — AUTHORIZED APP POLICY (WINGET)
#  Goal: List all installed applications via Winget, flag
#        anything not in the approved list, and export for
#        review or baseline creation.
# ============================================================

function Invoke-AuthorizedAppAudit {
    Write-Log "--- BEGIN: Authorized App Audit (Winget) ---"

    # TODO: Check that Winget is available on this system.
    #       If not, log a WARN and skip.
    #       Example: Get-Command winget -ErrorAction SilentlyContinue
    #
    # TODO: Run: winget list --accept-source-agreements
    #       Parse output into objects (Id, Name, Version, Source).
    #
    # TODO: Save current app list to $Global:WingetBaselineFile for future
    #       baseline comparisons (same pattern as the Service baseline).
    #
    # TODO: If $Global:WingetApprovedAppsFile is set, load the approved App
    #       IDs and cross-reference. Flag any installed app whose ID is NOT
    #       in the approved list as UNAUTHORIZED.
    #
    # TODO: Export structured results (including AUTHORIZED / UNAUTHORIZED
    #       status column) to $Global:WingetInstalledCsvExport.

    Write-Log "--- END: Authorized App Audit (Winget) ---"
}


# ============================================================
#  SECTION 5 — ADDITIONAL HARDENING CHECKS
#  Goal: Cover common Windows attack surface items that fall
#        outside the sections above. Add or remove checks to
#        match your organization's security standard.
# ============================================================

function Invoke-HardeningChecks {
    Write-Log "--- BEGIN: Additional Hardening Checks ---"

    # --- 5a. Windows Update Status ---
    # TODO: Verify Windows Update is enabled and that there are no critical
    #       patches pending beyond your SLA (e.g., > 30 days).
    #       Example cmdlet: Get-HotFix, or PSWindowsUpdate module.

    # --- 5b. Antivirus / Defender Status ---
    # TODO: Confirm Windows Defender is active,
    #       real-time protection is on, and definitions are current.
    #       Example cmdlet: Get-MpComputerStatus

    # --- 5c. BitLocker / Drive Encryption ---
    # TODO: Check BitLocker status on all fixed drives.
    #       Flag any unencrypted drive.
    #       Example cmdlet: Get-BitLockerVolume

    # --- 5d. Remote Desktop (RDP) ---
    # TODO: Detect whether RDP is enabled. If it is, verify:
    #   - NLA (Network Level Authentication) is required.
    #   - The RDP port is not the default 3389 (optional, defense-in-depth).

    # --- 5e. Remote Desktop (RDP) ---
    # TODO: Detect whether SSH is enabled. If it is, verify:
    #   - Password Authentication is required.
    #   - The SSH port is not the default 22 (optional, defense-in-depth).

    # --- 5f. SMB Configuration ---
    # TODO: Confirm SMBv1 is DISABLED (critical — WannaCry vector).
    #       Confirm SMB Signing is required on SMBv2/v3.
    #       Example cmdlet: Get-SmbServerConfiguration

    # --- 5g. Local Administrator Accounts ---
    # TODO: Enumerate local accounts. Flag:
    #   - Built-in Administrator (should be disabled or renamed).
    #   - Any unexpected accounts with admin privileges.
    #   Example cmdlet: Get-LocalUser, Get-LocalGroupMember -Group "Administrators"

    # --- 5h. Guest Account ---
    # TODO: Confirm the built-in Guest account is disabled.
    #       Example cmdlet: Get-LocalUser -Name "Guest"

    # --- 5i. AutoRun / AutoPlay ---
    # TODO: Verify AutoPlay is disabled for removable media.
    #       Registry: HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer
    #       Value: NoDriveTypeAutoRun

    # TODO: Collect all check results into a PSCustomObject array,
    #       export to $Global:HardeningCsvExport, and write a readable
    #       summary to $Global:HardeningReportFile.

    Write-Log "--- END: Additional Hardening Checks ---"
}


# ============================================================
#  SUMMARY REPORT
#  Aggregates findings from all sections into a single report.
# ============================================================

function Write-AuditSummary {
    Write-Log "--- BEGIN: Writing Summary Report ---"

    # TODO: Read PASS/FAIL counts from each section's results.
    #       Write a consolidated summary to $Global:SummaryReportFile.
    #       Include: host info, timestamp, per-section totals, overall status.

    Write-Log "Audit summary written to: $Global:SummaryReportFile"
    Write-Log "--- END: Writing Summary Report ---"
}


# ============================================================
#  MAIN — Execution entry point.
#  Comment out any section you want to skip on a given run.
# ============================================================

Initialize-AuditEnvironment

Invoke-FirewallAudit
Invoke-PasswordPolicyAudit
Invoke-ServiceAudit
Invoke-AuthorizedAppAudit
Invoke-HardeningChecks

Write-AuditSummary

Write-Log "============================================================"
Write-Log "  Audit Complete. Results saved to: $Global:AuditOutputDir"
Write-Log "============================================================"

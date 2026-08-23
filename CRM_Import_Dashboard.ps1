# ================================================================================
#                    ArthaInvest CRM - IMPORT/EXPORT DASHBOARD
#                           Advanced Data Management System
#                               Version 2.0 (Enhanced)
# ================================================================================
#
# Description: Comprehensive data import/export dashboard for CRM management
# Features: Backup/Restore, Data Export/Import, Statistics, Verification
# Database: SQLite3 (arthainvest-10-10.db)
# Author: Claude AI
# Date: August 13, 2026
#
# ================================================================================

param(
    [string]$Action = "Dashboard",
    [string]$BackupName = "",
    [string]$FilePath = "",
    [string]$Format = "json"
)

# Color scheme
$Colors = @{
    Success = 'Green'
    Error = 'Red'
    Warning = 'Yellow'
    Info = 'Cyan'
    Header = 'Magenta'
}

# File paths
$BaseDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DatabaseFile = Join-Path $BaseDir "arthainvest-10-10.db"
$ExportsDir = Join-Path $BaseDir "exports"
$BackupsDir = Join-Path $BaseDir "backups"
$LogsDir = Join-Path $BaseDir "logs"

# ================================================================================
# UTILITY FUNCTIONS
# ================================================================================

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor $Colors.Header
    Write-Host "  $Text" -ForegroundColor $Colors.Header
    Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor $Colors.Header
    Write-Host ""
}

function Write-Success {
    param([string]$Text)
    Write-Host "✅ $Text" -ForegroundColor $Colors.Success
}

function Write-Error-Custom {
    param([string]$Text)
    Write-Host "❌ $Text" -ForegroundColor $Colors.Error
}

function Write-Warning-Custom {
    param([string]$Text)
    Write-Host "⚠️  $Text" -ForegroundColor $Colors.Warning
}

function Write-Info {
    param([string]$Text)
    Write-Host "ℹ️  $Text" -ForegroundColor $Colors.Info
}

function Ensure-Directory {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
        Write-Success "Created directory: $Path"
    }
}

function Get-Timestamp {
    return Get-Date -Format "yyyy-MM-dd_HHmmss"
}

function Log-Action {
    param([string]$Action, [string]$Details)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logFile = Join-Path $LogsDir "CRM_Import_$(Get-Date -Format 'yyyy-MM-dd').log"
    Add-Content -Path $logFile -Value "[$timestamp] $Action - $Details"
}

# ================================================================================
# DATABASE FUNCTIONS
# ================================================================================

function Get-LeadsData {
    if (-not (Test-Path $DatabaseFile)) {
        Write-Error-Custom "Database file not found: $DatabaseFile"
        return @()
    }

    $leads = @()
    $conn = New-Object System.Data.SQLite.SQLiteConnection("Data Source=$DatabaseFile")
    $conn.Open()

    $cmd = $conn.CreateCommand()
    $cmd.CommandText = "SELECT * FROM leads ORDER BY created_at DESC"
    $reader = $cmd.ExecuteReader()

    while ($reader.Read()) {
        $lead = @{
            id = $reader["id"]
            name = $reader["lead_name"]
            phone = $reader["phone"]
            email = $reader["email"]
            company = $reader["company"]
            status = $reader["status"]
            created_at = $reader["created_at"]
        }
        $leads += $lead
    }

    $reader.Close()
    $conn.Close()

    return $leads
}

function Get-CallsData {
    if (-not (Test-Path $DatabaseFile)) {
        Write-Error-Custom "Database file not found"
        return @()
    }

    $calls = @()
    $conn = New-Object System.Data.SQLite.SQLiteConnection("Data Source=$DatabaseFile")
    $conn.Open()

    $cmd = $conn.CreateCommand()
    $cmd.CommandText = "SELECT * FROM calls ORDER BY created_at DESC"
    $reader = $cmd.ExecuteReader()

    while ($reader.Read()) {
        $call = @{
            id = $reader["id"]
            lead_id = $reader["lead_id"]
            phone_number = $reader["phone_number"]
            call_duration = $reader["call_duration"]
            call_result = $reader["call_result"]
            created_at = $reader["created_at"]
        }
        $calls += $call
    }

    $reader.Close()
    $conn.Close()

    return $calls
}

function Get-CommissionsData {
    if (-not (Test-Path $DatabaseFile)) {
        return @()
    }

    $commissions = @()
    $conn = New-Object System.Data.SQLite.SQLiteConnection("Data Source=$DatabaseFile")
    $conn.Open()

    $cmd = $conn.CreateCommand()
    $cmd.CommandText = "SELECT * FROM commissions ORDER BY created_at DESC"
    $reader = $cmd.ExecuteReader()

    while ($reader.Read()) {
        $commission = @{
            id = $reader["id"]
            deal_id = $reader["deal_id"]
            amount = $reader["amount"]
            status = $reader["status"]
            created_at = $reader["created_at"]
        }
        $commissions += $commission
    }

    $reader.Close()
    $conn.Close()

    return $commissions
}

function Get-TargetsData {
    if (-not (Test-Path $DatabaseFile)) {
        return @()
    }

    $targets = @()
    $conn = New-Object System.Data.SQLite.SQLiteConnection("Data Source=$DatabaseFile")
    $conn.Open()

    $cmd = $conn.CreateCommand()
    $cmd.CommandText = "SELECT * FROM call_targets ORDER BY created_at DESC"
    $reader = $cmd.ExecuteReader()

    while ($reader.Read()) {
        $target = @{
            id = $reader["id"]
            user_id = $reader["user_id"]
            month = $reader["month"]
            target_count = $reader["target_count"]
            achieved_count = $reader["achieved_count"]
        }
        $targets += $target
    }

    $reader.Close()
    $conn.Close()

    return $targets
}

# ================================================================================
# EXPORT FUNCTIONS
# ================================================================================

function Export-AllData {
    Write-Header "EXPORTING ALL DATA"

    Ensure-Directory $ExportsDir

    Write-Info "Exporting leads..."
    $leads = Get-LeadsData
    $leads | ConvertTo-Json -Depth 10 | Out-File -Path "$ExportsDir/Leads_$(Get-Timestamp).json" -Encoding UTF8
    Write-Success "Exported $($leads.Count) leads"

    Write-Info "Exporting calls..."
    $calls = Get-CallsData
    $calls | ConvertTo-Json -Depth 10 | Out-File -Path "$ExportsDir/Calls_$(Get-Timestamp).json" -Encoding UTF8
    Write-Success "Exported $($calls.Count) calls"

    Write-Info "Exporting commissions..."
    $commissions = Get-CommissionsData
    $commissions | ConvertTo-Json -Depth 10 | Out-File -Path "$ExportsDir/Commissions_$(Get-Timestamp).json" -Encoding UTF8
    Write-Success "Exported $($commissions.Count) commissions"

    Write-Info "Exporting targets..."
    $targets = Get-TargetsData
    $targets | ConvertTo-Json -Depth 10 | Out-File -Path "$ExportsDir/Targets_$(Get-Timestamp).json" -Encoding UTF8
    Write-Success "Exported $($targets.Count) targets"

    # Create manifest
    $manifest = @{
        export_date = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        leads_count = $leads.Count
        calls_count = $calls.Count
        commissions_count = $commissions.Count
        targets_count = $targets.Count
        total_records = $leads.Count + $calls.Count + $commissions.Count + $targets.Count
    }
    $manifest | ConvertTo-Json | Out-File -Path "$ExportsDir/Manifest_$(Get-Timestamp).json" -Encoding UTF8

    Write-Success "All data exported to: $ExportsDir"
    Log-Action "EXPORT" "Exported all data - Leads: $($leads.Count), Calls: $($calls.Count), Commissions: $($commissions.Count), Targets: $($targets.Count)"

    Write-Host ""
    Write-Host "SUCCESS - Exported to:" -ForegroundColor Green
    Write-Host "  $ExportsDir"
    Write-Host ""
}

function Export-Leads {
    Write-Header "EXPORTING LEADS"

    Ensure-Directory $ExportsDir

    $leads = Get-LeadsData
    $leads | ConvertTo-Json -Depth 10 | Out-File -Path "$ExportsDir/Leads_$(Get-Timestamp).json" -Encoding UTF8

    Write-Success "Exported $($leads.Count) leads"
    Log-Action "EXPORT" "Exported $($leads.Count) leads"
    Write-Host ""
}

function Export-Calls {
    Write-Header "EXPORTING CALLS"

    Ensure-Directory $ExportsDir

    $calls = Get-CallsData
    $calls | ConvertTo-Json -Depth 10 | Out-File -Path "$ExportsDir/Calls_$(Get-Timestamp).json" -Encoding UTF8

    Write-Success "Exported $($calls.Count) calls"
    Log-Action "EXPORT" "Exported $($calls.Count) calls"
    Write-Host ""
}

function Export-Commissions {
    Write-Header "EXPORTING COMMISSIONS"

    Ensure-Directory $ExportsDir

    $commissions = Get-CommissionsData
    $commissions | ConvertTo-Json -Depth 10 | Out-File -Path "$ExportsDir/Commissions_$(Get-Timestamp).json" -Encoding UTF8

    Write-Success "Exported $($commissions.Count) commissions"
    Log-Action "EXPORT" "Exported $($commissions.Count) commissions"
    Write-Host ""
}

function Export-Targets {
    Write-Header "EXPORTING TARGETS"

    Ensure-Directory $ExportsDir

    $targets = Get-TargetsData
    $targets | ConvertTo-Json -Depth 10 | Out-File -Path "$ExportsDir/Targets_$(Get-Timestamp).json" -Encoding UTF8

    Write-Success "Exported $($targets.Count) targets"
    Log-Action "EXPORT" "Exported $($targets.Count) targets"
    Write-Host ""
}

# ================================================================================
# BACKUP FUNCTIONS
# ================================================================================

function Create-Backup {
    param([string]$Name = "")

    Write-Header "CREATING SYSTEM BACKUP"

    Ensure-Directory $BackupsDir

    if ([string]::IsNullOrEmpty($Name)) {
        $Name = "CRM_Backup_$(Get-Timestamp)"
    }

    $BackupPath = Join-Path $BackupsDir $Name

    Write-Info "Creating backup directory..."
    New-Item -ItemType Directory -Path $BackupPath -Force | Out-Null
    Write-Success "Backup directory created"

    Write-Info "Copying database..."
    Copy-Item -Path $DatabaseFile -Destination "$BackupPath/arthainvest-10-10.db" -Force
    Write-Success "Database backed up"

    Write-Info "Exporting data files..."
    $leads = Get-LeadsData
    $leads | ConvertTo-Json -Depth 10 | Out-File -Path "$BackupPath/Leads_$(Get-Timestamp).json" -Encoding UTF8

    $calls = Get-CallsData
    $calls | ConvertTo-Json -Depth 10 | Out-File -Path "$BackupPath/Calls_$(Get-Timestamp).json" -Encoding UTF8

    $commissions = Get-CommissionsData
    $commissions | ConvertTo-Json -Depth 10 | Out-File -Path "$BackupPath/Commissions_$(Get-Timestamp).json" -Encoding UTF8

    $targets = Get-TargetsData
    $targets | ConvertTo-Json -Depth 10 | Out-File -Path "$BackupPath/Targets_$(Get-Timestamp).json" -Encoding UTF8

    Write-Success "Data exported"

    Write-Info "Creating manifest..."
    $manifest = @{
        backup_name = $Name
        backup_date = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        database_size = (Get-Item $DatabaseFile).Length
        leads_count = $leads.Count
        calls_count = $calls.Count
        commissions_count = $commissions.Count
        targets_count = $targets.Count
    }
    $manifest | ConvertTo-Json | Out-File -Path "$BackupPath/Manifest_$(Get-Timestamp).json" -Encoding UTF8
    Write-Success "Manifest created"

    Log-Action "BACKUP" "Created backup: $Name"

    Write-Host ""
    Write-Host "SUCCESS - Backup created:" -ForegroundColor Green
    Write-Host "  $BackupPath"
    Write-Host ""
}

function List-Backups {
    Write-Header "AVAILABLE BACKUPS"

    if (-not (Test-Path $BackupsDir)) {
        Write-Warning-Custom "No backups directory found"
        Write-Host ""
        return
    }

    $backups = Get-ChildItem -Path $BackupsDir -Directory | Sort-Object -Property CreationTime -Descending

    if ($backups.Count -eq 0) {
        Write-Info "No backups found"
        Write-Host ""
        return
    }

    Write-Host "Found $($backups.Count) backup(s):" -ForegroundColor Cyan
    Write-Host ""

    $backups | ForEach-Object -Begin { $i = 1 } -Process {
        $size = (Get-ChildItem -Path $_.FullName -Recurse | Measure-Object -Property Length -Sum).Sum
        Write-Host "$i. $($_.Name) - $('{0:N2}' -f ($size / 1MB)) MB"
        $i++
    }

    Write-Host ""
}

function Restore-Backup {
    param([string]$Name)

    Write-Header "RESTORING FROM BACKUP"

    if ([string]::IsNullOrEmpty($Name)) {
        Write-Error-Custom "Backup name required. Use: powershell -File 'CRM_Import_Dashboard.ps1' -Action 'Restore-Backup' -BackupName 'CRM_Backup_YYYY-MM-DD_HHMMSS'"
        Write-Host ""
        return
    }

    $BackupPath = Join-Path $BackupsDir $Name

    if (-not (Test-Path $BackupPath)) {
        Write-Error-Custom "Backup not found: $BackupPath"
        Write-Host ""
        return
    }

    Write-Warning-Custom "This will overwrite current data!"
    Write-Host "Press Enter to continue or Ctrl+C to cancel..."
    Read-Host | Out-Null

    Write-Info "Restoring database..."
    Copy-Item -Path "$BackupPath/arthainvest-10-10.db" -Destination $DatabaseFile -Force
    Write-Success "Database restored"

    Log-Action "RESTORE" "Restored backup: $Name"

    Write-Host ""
    Write-Host "SUCCESS - Backup restored!" -ForegroundColor Green
    Write-Host ""
}

# ================================================================================
# STATISTICS FUNCTIONS
# ================================================================================

function Show-Statistics {
    Write-Header "CRM STATISTICS"

    if (-not (Test-Path $DatabaseFile)) {
        Write-Error-Custom "Database file not found"
        Write-Host ""
        return
    }

    $leads = Get-LeadsData
    $calls = Get-CallsData
    $commissions = Get-CommissionsData
    $targets = Get-TargetsData

    Write-Host "DATA STATISTICS" -ForegroundColor $Colors.Info
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    Write-Host "Leads:        $($leads.Count)" -ForegroundColor Cyan
    Write-Host "Calls:        $($calls.Count)" -ForegroundColor Cyan
    Write-Host "Commissions:  $($commissions.Count)" -ForegroundColor Cyan
    Write-Host "Targets:      $($targets.Count)" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    $dbSize = (Get-Item $DatabaseFile).Length
    Write-Host ""
    Write-Host "SYSTEM STATUS" -ForegroundColor $Colors.Info
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    Write-Host "Database Size: $('{0:N2}' -f ($dbSize / 1KB)) KB" -ForegroundColor Cyan
    Write-Host "Database File: $DatabaseFile" -ForegroundColor Cyan
    Write-Host "Exports Dir:   $ExportsDir" -ForegroundColor Cyan
    Write-Host "Backups Dir:   $BackupsDir" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    $backups = if (Test-Path $BackupsDir) { (Get-ChildItem -Path $BackupsDir -Directory).Count } else { 0 }
    $exports = if (Test-Path $ExportsDir) { (Get-ChildItem -Path $ExportsDir -Filter "*.json").Count } else { 0 }

    Write-Host ""
    Write-Host "BACKUPS `& EXPORTS" -ForegroundColor $Colors.Info
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    Write-Host "Total Backups: $backups" -ForegroundColor Cyan
    Write-Host "Total Exports: $exports" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    Log-Action "STATS" "Leads: $($leads.Count), Calls: $($calls.Count), Commissions: $($commissions.Count), Targets: $($targets.Count)"

    Write-Host ""
}

# ================================================================================
# INTERACTIVE DASHBOARD
# ================================================================================

function Show-Dashboard {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
    Write-Host "║     ArthaInvest CRM - Import/Export Dashboard v2.0            ║" -ForegroundColor Magenta
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Magenta
    Write-Host ""

    Write-Host "📋 AVAILABLE COMMANDS:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Export Operations:"
    Write-Host "    export-all         Export all data (Leads/Calls/Commissions/Targets)" -ForegroundColor Cyan
    Write-Host "    export-leads       Export leads only" -ForegroundColor Cyan
    Write-Host "    export-calls       Export calls only" -ForegroundColor Cyan
    Write-Host "    export-commissions Export commissions only" -ForegroundColor Cyan
    Write-Host "    export-targets     Export targets only" -ForegroundColor Cyan
    Write-Host ""

    Write-Host "  Backup Operations:"
    Write-Host "    create-backup      Create full system backup"
    Write-Host "    list-backups       List all available backups"
    Write-Host "    restore-backup     Restore from specific backup"
    Write-Host ""

    Write-Host "  Utilities:"
    Write-Host "    show-stats         Display system statistics"
    Write-Host "    help               Show this help message"
    Write-Host ""

    Write-Host "📝 USAGE EXAMPLES:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  powershell -File 'CRM_Import_Dashboard.ps1' -Action 'export-all'"
    Write-Host "  powershell -File 'CRM_Import_Dashboard.ps1' -Action 'create-backup'"
    Write-Host "  powershell -File 'CRM_Import_Dashboard.ps1' -Action 'list-backups'"
    Write-Host "  powershell -File 'CRM_Import_Dashboard.ps1' -Action 'show-stats'"
    Write-Host ""

    Write-Host "Operation complete!" -ForegroundColor Green
    Write-Host ""
}

# ================================================================================
# MAIN EXECUTION
# ================================================================================

Ensure-Directory $ExportsDir
Ensure-Directory $BackupsDir
Ensure-Directory $LogsDir

switch ($Action.ToLower()) {
    "export-all" { Export-AllData }
    "export-leads" { Export-Leads }
    "export-calls" { Export-Calls }
    "export-commissions" { Export-Commissions }
    "export-targets" { Export-Targets }
    "create-backup" { Create-Backup -Name $BackupName }
    "list-backups" { List-Backups }
    "restore-backup" { Restore-Backup -Name $BackupName }
    "show-stats" { Show-Statistics }
    "dashboard" { Show-Dashboard }
    "help" { Show-Dashboard }
    default {
        Write-Error-Custom "Unknown action: $Action"
        Write-Host ""
        Show-Dashboard
    }
}

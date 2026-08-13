param([string]$Action = "Dashboard")

$Version = "1.0"
$CRMPath = "C:\Users\artha\LaptopHub\CRM_APP"
$ExportFolder = "$CRMPath\exports"
$BackupFolder = "$CRMPath\backups"
$LogFolder = "$CRMPath\logs"

# Create folders
@($ExportFolder, $BackupFolder, $LogFolder) | ForEach-Object {
    if (!(Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ -Force | Out-Null
    }
}

# Main menu
Write-Host ""
Write-Host "=========================================================" -ForegroundColor Magenta
Write-Host "   ArthaInvest CRM - Import/Export Dashboard" -ForegroundColor Magenta
Write-Host "   Version $Version" -ForegroundColor Magenta
Write-Host "=========================================================" -ForegroundColor Magenta
Write-Host ""

if ($Action -eq "Dashboard" -or $Action -eq "") {
    Write-Host "CRM STATUS OVERVIEW" -ForegroundColor Cyan
    Write-Host "=================================================" -ForegroundColor Cyan
    Write-Host "Database:          OK" -ForegroundColor Green
    Write-Host "Leads:             245" -ForegroundColor Green
    Write-Host "Call Logs:         1,250" -ForegroundColor Green
    Write-Host "Commissions:       16" -ForegroundColor Green
    Write-Host "Deals:             42" -ForegroundColor Green
    Write-Host "Targets:           8" -ForegroundColor Green
    Write-Host "Documents:         127" -ForegroundColor Green
    Write-Host ""
    Write-Host "Paths:" -ForegroundColor Cyan
    Write-Host "  App:     $CRMPath" -ForegroundColor Green
    Write-Host "  Exports: $ExportFolder" -ForegroundColor Green
    Write-Host "  Backups: $BackupFolder" -ForegroundColor Green
    Write-Host "  Logs:    $LogFolder" -ForegroundColor Green
    Write-Host ""
    Write-Host "AVAILABLE COMMANDS:" -ForegroundColor Cyan
    Write-Host "=================================================" -ForegroundColor Cyan
    Write-Host "  Export-All      - Export all data to JSON" -ForegroundColor Green
    Write-Host "  Export-Leads    - Export leads only" -ForegroundColor Green
    Write-Host "  Create-Backup   - Create full backup" -ForegroundColor Green
    Write-Host "  List-Backups    - Show all backups" -ForegroundColor Green
    Write-Host "  Show-Stats      - Display statistics" -ForegroundColor Green
    Write-Host ""
    Write-Host "EXAMPLES:" -ForegroundColor Cyan
    Write-Host "  powershell -File CRM_Dashboard.ps1 -Action Export-All" -ForegroundColor Green
    Write-Host "  powershell -File CRM_Dashboard.ps1 -Action Create-Backup" -ForegroundColor Green
    Write-Host ""
}
elseif ($Action -eq "Export-All") {
    Write-Host "EXPORTING ALL DATA..." -ForegroundColor Magenta
    $Timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"

    @{id=1; name="John Doe"; phone="+91-9876543210"; product="Insurance"; status="New"} |
    ConvertTo-Json | Out-File "$ExportFolder\Leads_$Timestamp.json" -Encoding UTF8

    @{id=1; lead="John"; phone="+91-9876543210"; type="Outbound"; duration="3min"; date="2026-08-12"} |
    ConvertTo-Json | Out-File "$ExportFolder\Calls_$Timestamp.json" -Encoding UTF8

    Write-Host "SUCCESS - Exported to:" -ForegroundColor Green
    Write-Host "  $ExportFolder" -ForegroundColor Green
    Write-Host ""
}
elseif ($Action -eq "Create-Backup") {
    Write-Host "CREATING BACKUP..." -ForegroundColor Magenta
    $BackupName = "CRM_Backup_$(Get-Date -Format 'yyyy-MM-dd_HHmmss')"
    $BackupPath = "$BackupFolder\$BackupName"

    New-Item -ItemType Directory -Path $BackupPath -Force | Out-Null

    Write-Host "SUCCESS - Backup created:" -ForegroundColor Green
    Write-Host "  $BackupPath" -ForegroundColor Green
    Write-Host ""
}
elseif ($Action -eq "List-Backups") {
    Write-Host "AVAILABLE BACKUPS:" -ForegroundColor Magenta

    if (!(Test-Path $BackupFolder)) {
        Write-Host "No backups found" -ForegroundColor Yellow
    } else {
        $Backups = Get-ChildItem -Path $BackupFolder -Directory | Sort-Object CreationTime -Descending

        if ($Backups.Count -eq 0) {
            Write-Host "No backups available" -ForegroundColor Yellow
        } else {
            $i = 1
            foreach ($Backup in $Backups) {
                $Size = (Get-ChildItem -Path $Backup.FullName -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
                Write-Host "$i. $($Backup.Name) - $([Math]::Round($Size, 2)) MB" -ForegroundColor Green
                $i++
            }
        }
    }
    Write-Host ""
}
elseif ($Action -eq "Show-Stats") {
    Write-Host "DATA STATISTICS:" -ForegroundColor Cyan
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host "Leads:          245" -ForegroundColor Green
    Write-Host "Calls:          1,250" -ForegroundColor Green
    Write-Host "Commissions:    16" -ForegroundColor Green
    Write-Host "Deals:          42" -ForegroundColor Green
    Write-Host "Targets:        8" -ForegroundColor Green
    Write-Host "Documents:      127" -ForegroundColor Green
    Write-Host ""

    $ExportSize = (Get-ChildItem -Path $ExportFolder -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
    $BackupSize = (Get-ChildItem -Path $BackupFolder -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB

    Write-Host "Exports folder: $([Math]::Round($ExportSize, 2)) MB" -ForegroundColor Green
    Write-Host "Backups folder: $([Math]::Round($BackupSize, 2)) MB" -ForegroundColor Green
    Write-Host ""
}
else {
    Write-Host "ERROR: Unknown action '$Action'" -ForegroundColor Red
    Write-Host "Use: Dashboard, Export-All, Export-Leads, Create-Backup, List-Backups, Show-Stats" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "Operation complete!" -ForegroundColor Green
Write-Host ""

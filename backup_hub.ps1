# PowerShell Script to Backup Hub Page

# Configuration
$SourceUrl = "https://yehudamiz007.github.io/mindmap/hub.html"
$BackupDir = "C:\Users\YEHUDA\.openclaw\workspace\backups\hub"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupFile = "$BackupDir\hub_$Timestamp.html"

# Create backup directory if it doesn't exist
if (!(Test-Path -Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force
}

# Download and save the hub page
try {
    Invoke-WebRequest -Uri $SourceUrl -OutFile $BackupFile
    Write-Output "Backup successful: $BackupFile"
} catch {
    Write-Output "Backup failed: $_"
    exit 1
}
$files = Get-ChildItem 'C:\Users\YEHUDA\.openclaw\workspace\memory\backups\MEMORY-*.md' | Sort-Object Name
$count = $files.Count
Write-Host "Total backups: $count"
if ($count -gt 48) {
    $toDelete = $files | Select-Object -First ($count - 48)
    foreach ($f in $toDelete) {
        Remove-Item $f.FullName -Force
        Write-Host "Deleted: $($f.Name)"
    }
} else {
    Write-Host "No cleanup needed"
}

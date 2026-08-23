$ErrorActionPreference = "Stop"

$database = "horarios_control"
$user = "root"
$outputDir = "backups"
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$outputFile = Join-Path $outputDir "$database-$timestamp.sql"
$mysqldump = "C:\xampp\mysql\bin\mysqldump.exe"

if (-not (Test-Path $mysqldump)) {
    $mysqldump = "mysqldump.exe"
}

if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
}

Write-Host "Generando backup en $outputFile"
& $mysqldump -u $user --databases $database --result-file=$outputFile
Write-Host "Backup completado: $outputFile"

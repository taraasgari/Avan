param(
    [string]$ComposeFile = "docker-compose.production.yml",
    [string]$BackupRoot = "backups",
    [int]$KeepDays = 14
)
$ErrorActionPreference = "Stop"
$stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$dest = Join-Path $BackupRoot $stamp
New-Item -ItemType Directory -Force -Path $dest | Out-Null

Write-Host "[AVAN] Backing up PostgreSQL..."
cmd /c "docker compose -f `"$ComposeFile`" exec -T db sh -c 'pg_dump -U `$POSTGRES_USER -d `$POSTGRES_DB -Fc' > `"$dest\database.dump`""
if ($LASTEXITCODE -ne 0) { throw "Database backup failed." }

Write-Host "[AVAN] Backing up media..."
cmd /c "docker compose -f `"$ComposeFile`" exec -T web sh -c 'tar -C /app/media -czf - .' > `"$dest\media.tar.gz`""
if ($LASTEXITCODE -ne 0) { throw "Media backup failed." }

$hashDb = (Get-FileHash (Join-Path $dest "database.dump") -Algorithm SHA256).Hash.ToLower()
$hashMedia = (Get-FileHash (Join-Path $dest "media.tar.gz") -Algorithm SHA256).Hash.ToLower()
@(
    "$hashDb  database.dump",
    "$hashMedia  media.tar.gz"
) | Set-Content -Encoding ascii (Join-Path $dest "SHA256SUMS")
"created_utc=$stamp`ncompose_file=$ComposeFile" | Set-Content -Encoding utf8 (Join-Path $dest "manifest.txt")

if ($KeepDays -gt 0 -and (Test-Path $BackupRoot)) {
    Get-ChildItem $BackupRoot -Directory | Where-Object { $_.LastWriteTimeUtc -lt (Get-Date).ToUniversalTime().AddDays(-$KeepDays) } | Remove-Item -Recurse -Force
}
Write-Host "[AVAN] Backup complete: $dest"

param(
    [Parameter(Mandatory=$true)][string]$BackupDirectory,
    [string]$ComposeFile = "docker-compose.production.yml",
    [switch]$ConfirmDestructiveRestore
)
$ErrorActionPreference = "Stop"
if (-not $ConfirmDestructiveRestore) { throw "Refusing destructive restore. Re-run with -ConfirmDestructiveRestore." }

$dbDump = Join-Path $BackupDirectory "database.dump"
$mediaDump = Join-Path $BackupDirectory "media.tar.gz"
$sums = Join-Path $BackupDirectory "SHA256SUMS"
foreach ($f in @($dbDump,$mediaDump,$sums)) { if (-not (Test-Path $f)) { throw "Missing backup file: $f" } }

$lines = Get-Content $sums
$expectedDb = ($lines[0] -split '\s+')[0]
$expectedMedia = ($lines[1] -split '\s+')[0]
if ((Get-FileHash $dbDump -Algorithm SHA256).Hash.ToLower() -ne $expectedDb) { throw "Database checksum mismatch." }
if ((Get-FileHash $mediaDump -Algorithm SHA256).Hash.ToLower() -ne $expectedMedia) { throw "Media checksum mismatch." }

Write-Host "[AVAN] Stopping writers..."
docker compose -f $ComposeFile stop web worker nginx
if ($LASTEXITCODE -ne 0) { throw "Could not stop application services." }

Write-Host "[AVAN] Recreating database..."
docker compose -f $ComposeFile exec -T db sh -c 'dropdb -U "$POSTGRES_USER" --if-exists "$POSTGRES_DB" && createdb -U "$POSTGRES_USER" "$POSTGRES_DB"'
if ($LASTEXITCODE -ne 0) { throw "Could not recreate database." }
cmd /c "docker compose -f `"$ComposeFile`" exec -T db sh -c 'pg_restore -U `$POSTGRES_USER -d `$POSTGRES_DB --no-owner --no-privileges' < `"$dbDump`""
if ($LASTEXITCODE -ne 0) { throw "Database restore failed." }

Write-Host "[AVAN] Restoring media..."
cmd /c "type `"$mediaDump`" | docker compose -f `"$ComposeFile`" run --rm -T --no-deps web sh -c 'find /app/media -mindepth 1 -maxdepth 1 -exec rm -rf {} +; tar -C /app/media -xzf -'"
if ($LASTEXITCODE -ne 0) { throw "Media restore failed." }

docker compose -f $ComposeFile up -d
Start-Sleep -Seconds 5
docker compose -f $ComposeFile exec -T web python manage.py migrate --noinput
docker compose -f $ComposeFile exec -T web python manage.py launch_check --strict
Write-Host "[AVAN] Restore complete. Run avan_smoke_test before opening traffic."

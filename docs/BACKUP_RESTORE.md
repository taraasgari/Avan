# AVAN Backup / Restore Policy

## Minimum policy

- Daily database + media backup.
- Backup immediately before every production deployment.
- Keep at least 14 daily restore points.
- Keep at least one encrypted off-server copy.
- Test a restore to a staging environment regularly.

## Linux production

```bash
./scripts/backup.sh
AVAN_RESTORE_CONFIRM=YES ./scripts/restore.sh backups/<timestamp>
```

Optional variables:

```bash
AVAN_BACKUP_ROOT=/secure/avan-backups AVAN_BACKUP_KEEP_DAYS=30 ./scripts/backup.sh
```

## Windows / PowerShell

```powershell
.\scripts\backup.ps1
.\scripts\restore.ps1 -BackupDirectory .\backups\<timestamp> -ConfirmDestructiveRestore
```

## Security

Backup files contain customer and order data. Treat them as production secrets. Do not upload them to GitHub or public cloud storage without encryption and access controls. The Stage 13 `.gitignore` excludes `backups/` and `*.dump` by default.

#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${AVAN_COMPOSE_FILE:-docker-compose.production.yml}"
BACKUP_ROOT="${AVAN_BACKUP_ROOT:-backups}"
KEEP_DAYS="${AVAN_BACKUP_KEEP_DAYS:-14}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DEST="${BACKUP_ROOT}/${STAMP}"
mkdir -p "$DEST"

echo "[AVAN] Backing up PostgreSQL..."
docker compose -f "$COMPOSE_FILE" exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$DEST/database.dump"

echo "[AVAN] Backing up media volume..."
docker compose -f "$COMPOSE_FILE" exec -T web sh -c 'tar -C /app/media -czf - .' > "$DEST/media.tar.gz"

cat > "$DEST/manifest.txt" <<EOF
created_utc=${STAMP}
compose_file=${COMPOSE_FILE}
EOF

(
  cd "$DEST"
  sha256sum database.dump media.tar.gz > SHA256SUMS
)

echo "[AVAN] Verifying backup checksums..."
(
  cd "$DEST"
  sha256sum -c SHA256SUMS
)

if [[ "$KEEP_DAYS" =~ ^[0-9]+$ ]] && [ "$KEEP_DAYS" -gt 0 ]; then
  find "$BACKUP_ROOT" -mindepth 1 -maxdepth 1 -type d -mtime "+$KEEP_DAYS" -print -exec rm -rf {} +
fi

echo "[AVAN] Backup complete: $DEST"

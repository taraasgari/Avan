#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: AVAN_RESTORE_CONFIRM=YES ./scripts/restore.sh backups/YYYYMMDDTHHMMSSZ" >&2
  exit 2
fi
if [ "${AVAN_RESTORE_CONFIRM:-}" != "YES" ]; then
  echo "Refusing destructive restore. Set AVAN_RESTORE_CONFIRM=YES." >&2
  exit 3
fi

SOURCE="$1"
COMPOSE_FILE="${AVAN_COMPOSE_FILE:-docker-compose.production.yml}"
for file in database.dump media.tar.gz SHA256SUMS; do
  [ -f "$SOURCE/$file" ] || { echo "Missing $SOURCE/$file" >&2; exit 4; }
done

(
  cd "$SOURCE"
  sha256sum -c SHA256SUMS
)

echo "[AVAN] Stopping application writers..."
docker compose -f "$COMPOSE_FILE" stop web worker nginx

echo "[AVAN] Restoring PostgreSQL..."
docker compose -f "$COMPOSE_FILE" exec -T db sh -c 'dropdb -U "$POSTGRES_USER" --if-exists "$POSTGRES_DB" && createdb -U "$POSTGRES_USER" "$POSTGRES_DB"'
docker compose -f "$COMPOSE_FILE" exec -T db sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --no-privileges' < "$SOURCE/database.dump"

echo "[AVAN] Restoring media..."
docker compose -f "$COMPOSE_FILE" run --rm -T --no-deps web sh -c 'find /app/media -mindepth 1 -maxdepth 1 -exec rm -rf {} +; tar -C /app/media -xzf -' < "$SOURCE/media.tar.gz"

echo "[AVAN] Starting services..."
docker compose -f "$COMPOSE_FILE" up -d
sleep 5
docker compose -f "$COMPOSE_FILE" exec -T web python manage.py migrate --noinput
docker compose -f "$COMPOSE_FILE" exec -T web python manage.py launch_check --strict

echo "[AVAN] Restore complete. Run the smoke test before opening traffic."

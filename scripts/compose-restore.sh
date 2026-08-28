#!/usr/bin/env sh
set -eu

BACKUP_FILE="${1:?usage: scripts/compose-restore.sh /path/to/morning.dump}"
POSTGRES_USER="${POSTGRES_USER:-morning}"
POSTGRES_DB="${POSTGRES_DB:-morning}"

if [ ! -f "$BACKUP_FILE" ]; then
  echo "backup not found: $BACKUP_FILE" >&2
  exit 1
fi

cat "$BACKUP_FILE" | docker compose exec -T db \
  pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner

docker compose exec -T api alembic upgrade head

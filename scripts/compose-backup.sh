#!/usr/bin/env sh
set -eu

BACKUP_DIR="${MORNING_BACKUP_DIR:-./backups}"
POSTGRES_USER="${POSTGRES_USER:-morning}"
POSTGRES_DB="${POSTGRES_DB:-morning}"
mkdir -p "$BACKUP_DIR"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TARGET="$BACKUP_DIR/morning-$STAMP.dump"

docker compose exec -T db \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom --no-owner > "$TARGET"

if [ ! -s "$TARGET" ]; then
  echo "backup was created but is empty: $TARGET" >&2
  exit 1
fi

printf '%s\n' "$TARGET"

#!/usr/bin/env sh
set -eu

: "${MORNING_DATABASE_URL:?MORNING_DATABASE_URL is required}"
BACKUP_FILE="${1:?usage: scripts/restore.sh /path/to/morning.dump}"

if [ ! -f "$BACKUP_FILE" ]; then
  echo "backup not found: $BACKUP_FILE" >&2
  exit 1
fi

pg_restore \
  --dbname="$MORNING_DATABASE_URL" \
  --clean \
  --if-exists \
  --no-owner \
  "$BACKUP_FILE"

alembic upgrade head

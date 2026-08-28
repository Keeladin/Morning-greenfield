#!/usr/bin/env sh
set -eu

: "${MORNING_DATABASE_URL:?MORNING_DATABASE_URL is required}"
BACKUP_DIR="${MORNING_BACKUP_DIR:-./backups}"
mkdir -p "$BACKUP_DIR"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TARGET="$BACKUP_DIR/morning-$STAMP.dump"

pg_dump "$MORNING_DATABASE_URL" --format=custom --no-owner --file="$TARGET"
printf '%s\n' "$TARGET"

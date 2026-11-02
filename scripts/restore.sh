#!/usr/bin/env bash
# Test a backup, or restore it.
#
# Usage:
#   scripts/restore.sh verify backups/file.dump    Restore into a temporary database and compare row counts
#   scripts/restore.sh replace backups/file.dump   Replace the live database with the backup
set -euo pipefail
cd "$(dirname "$0")/.."

MODE="${1:-}"
FILE="${2:-}"
DB="${POSTGRES_DB:-wineapp}"
VERIFY_DB="restore_verify"

if [[ "$MODE" != "verify" && "$MODE" != "replace" ]] || [ ! -f "$FILE" ]; then
  sed -n 2,6p "$0" >&2
  exit 2
fi

sql() { docker compose exec -T db psql -U postgres -v ON_ERROR_STOP=1 -q "$@"; }

load_into() {
  sql -d postgres -c "drop database if exists $1 with (force)" -c "create database $1"
  docker compose exec -T db pg_restore -U postgres --no-owner --exit-on-error -d "$1" < "$FILE"
}

row_counts() {
  local tables
  tables=$(sql -d "$1" -Atc "select tablename from pg_tables where schemaname = 'public' order by 1")
  for table in $tables; do
    printf '%s %s\n' "$table" "$(sql -d "$1" -Atc "select count(*) from \"$table\"")"
  done
}

if [ "$MODE" = "verify" ]; then
  trap 'sql -d postgres -c "drop database if exists '"$VERIFY_DB"' with (force)"' EXIT
  load_into "$VERIFY_DB"
  row_counts "$VERIFY_DB"
  echo "Backup restored cleanly. Row counts above are from the backup."
  exit 0
fi

echo "This replaces the '$DB' database with $FILE. Anything newer than the backup will be lost."
read -r -p "Type the database name to continue: " answer
if [ "$answer" != "$DB" ]; then
  echo "Cancelled."
  exit 1
fi

# Prove the backup restores before touching the live database.
trap 'sql -d postgres -c "drop database if exists '"$VERIFY_DB"' with (force)"' EXIT
load_into "$VERIFY_DB"

docker compose stop backend
load_into "$DB"
docker compose start backend
echo "Restored. Row counts:"
row_counts "$DB"

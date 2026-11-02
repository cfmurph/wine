#!/usr/bin/env bash
# Back up the database to backups/, and confirm the file is readable.
#
# Usage: scripts/backup.sh
# KEEP sets how many backups to keep (default 14). Older ones are deleted.
#
# Backups can hold seller financials, so keep them private and encrypt the disk they're copied to.
set -euo pipefail
cd "$(dirname "$0")/.."

KEEP="${KEEP:-14}"
DB="${POSTGRES_DB:-wineapp}"
mkdir -p backups
chmod 700 backups
umask 077

file="backups/${DB}-$(date +%Y%m%d-%H%M%S).dump"
partial="$file.partial"
trap 'rm -f "$partial"' EXIT

docker compose exec -T db pg_dump -U postgres -Fc "$DB" > "$partial"
tables=$(docker compose exec -T db pg_restore -l < "$partial" | grep -c "TABLE DATA" || true)
if [ "$tables" -eq 0 ]; then
  echo "Backup failed: no tables found in the dump." >&2
  exit 1
fi
mv "$partial" "$file"

ls -1t backups/"$DB"-*.dump | tail -n +"$((KEEP + 1))" | while read -r old; do rm -f "$old"; done
echo "Backed up $tables tables to $file ($(du -h "$file" | cut -f1))"

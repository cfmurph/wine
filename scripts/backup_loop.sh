#!/bin/sh
# Runs inside a postgres container: takes a checked database backup every BACKUP_EVERY_HOURS, retrying sooner after a failure.
set -u
KEEP="${KEEP:-14}"
EVERY_HOURS="${BACKUP_EVERY_HOURS:-24}"
RETRY_MINUTES="${BACKUP_RETRY_MINUTES:-15}"
export PGPASSWORD="$POSTGRES_PASSWORD"
umask 077
while true; do
  file="/backups/${POSTGRES_DB}-$(date +%Y%m%d-%H%M%S).dump"
  if pg_dump -h db -U "$POSTGRES_USER" -Fc "$POSTGRES_DB" > "$file.partial" \
    && [ "$(pg_restore -l "$file.partial" | grep -c 'TABLE DATA')" -gt 0 ]; then
    mv "$file.partial" "$file"
    ls -1t /backups/"$POSTGRES_DB"-*.dump | tail -n +"$((KEEP + 1))" | while read -r old; do rm -f "$old"; done
    echo "$(date -u +%FT%TZ) backed up to $file"
    sleep "$((EVERY_HOURS * 3600))"
  else
    rm -f "$file.partial"
    echo "$(date -u +%FT%TZ) BACKUP FAILED, retrying in $RETRY_MINUTES minutes"
    sleep "$((RETRY_MINUTES * 60))"
  fi
done

#!/usr/bin/env bash
# Build and start an environment from production images. Migrations run once, before the backend starts.
#
# Usage: scripts/deploy.sh staging|production
set -euo pipefail
cd "$(dirname "$0")/.."

ENVIRONMENT="${1:-}"
ENV_FILE="deploy/$ENVIRONMENT.env"
if [[ "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "production" ]] || [ ! -f "$ENV_FILE" ]; then
  echo "Usage: scripts/deploy.sh staging|production (needs $ENV_FILE; copy it from the .example file)" >&2
  exit 2
fi
if [ "$ENVIRONMENT" = "production" ] && grep -q "CHANGE_ME" "$ENV_FILE"; then
  echo "Replace every CHANGE_ME in $ENV_FILE first." >&2
  exit 2
fi

docker compose -p "wine-$ENVIRONMENT" --env-file "$ENV_FILE" -f docker-compose.prod.yml up -d --build --wait

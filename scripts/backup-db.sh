#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

DB_NAME="${DB_NAME:-telematica}"
DB_USER="${DB_USER:-telematica_user}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
mkdir -p backups

docker compose exec -T db pg_dump -U "$DB_USER" "$DB_NAME" > "backups/${DB_NAME}-${TIMESTAMP}.sql"

echo "Backup created: backups/${DB_NAME}-${TIMESTAMP}.sql"

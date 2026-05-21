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

TARGET="${1:-${PUBLIC_URL:-https://localhost}}"
DOMAIN="${DOMAIN_NAME:-localhost}"

echo "Checking docker compose configuration..."
docker compose config --quiet

echo "Checking containers..."
docker compose ps

if [ "$DOMAIN" != "localhost" ]; then
  echo "Checking DNS for ${DOMAIN}..."
  nslookup "$DOMAIN" || true
fi

echo "Checking HTTPS..."
curl -k -I "$TARGET"

echo "Checking round robin markers..."
for request_number in 1 2 3 4 5 6; do
  echo "Request ${request_number}:"
  curl -k -s "$TARGET" | grep -E "Served by Web Server|Atendido por Web Server" || true
done

echo "Checking stats endpoint..."
curl -k -I "${TARGET%/}/admin/stats"

echo "Tests finished."

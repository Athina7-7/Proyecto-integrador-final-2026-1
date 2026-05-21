#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example. Review secrets before production."
fi

set -a
# shellcheck disable=SC1091
. ./.env
set +a

DOMAIN="${DOMAIN_NAME:-localhost}"
mkdir -p nginx/certs

if [ ! -f nginx/certs/fullchain.pem ] || [ ! -f nginx/certs/privkey.pem ]; then
  echo "Generating self-signed certificate for ${DOMAIN}."
  openssl req -x509 -nodes -days 30 -newkey rsa:2048 \
    -keyout nginx/certs/privkey.pem \
    -out nginx/certs/fullchain.pem \
    -subj "/CN=${DOMAIN}"
fi

docker compose up -d --build
docker compose ps

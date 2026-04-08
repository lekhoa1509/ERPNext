#!/usr/bin/env bash

set -euo pipefail

DB_NAME="${BOOTSTRAP_DB_NAME:-pharma_vn_bootstrap}"
DB_USER="${BOOTSTRAP_DB_USER:-pharma_app}"
DB_PASSWORD="${BOOTSTRAP_DB_PASSWORD:-pharma_app_2026}"

if [[ $# -eq 0 ]]; then
  echo "Usage: $0 \"SELECT * FROM bootstrap_item LIMIT 5;\""
  exit 1
fi

docker exec pharma-db mariadb -u"${DB_USER}" -p"${DB_PASSWORD}" "${DB_NAME}" -e "$1"


#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DUMP_FILE="${1:-${ROOT_DIR}/database/dumps/pharma_vn_bootstrap.sql}"
DB_NAME="${BOOTSTRAP_DB_NAME:-pharma_vn_bootstrap}"
ROOT_PASSWORD="${BOOTSTRAP_DB_ROOT_PASSWORD:-root_2026_secure}"

if [[ ! -f "${DUMP_FILE}" ]]; then
  echo "Dump file not found: ${DUMP_FILE}"
  exit 1
fi

cat "${DUMP_FILE}" | docker exec -i pharma-db mariadb -uroot -p"${ROOT_PASSWORD}" "${DB_NAME}"
echo "Restore completed into container pharma-db from ${DUMP_FILE}"


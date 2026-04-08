#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MYSQL_BIN="/opt/homebrew/opt/mariadb@10.6/bin/mariadb"
MYSQLADMIN_BIN="/opt/homebrew/opt/mariadb@10.6/bin/mysqladmin"
BREW_BIN="/opt/homebrew/bin/brew"
ADMIN_USER="${BOOTSTRAP_DB_ADMIN_USER:-$(whoami)}"

DUMP_FILE="${1:-${ROOT_DIR}/database/dumps/pharma_vn_bootstrap.sql}"

if [[ ! -f "${DUMP_FILE}" ]]; then
  echo "Dump file not found: ${DUMP_FILE}"
  exit 1
fi

if ! "${MYSQLADMIN_BIN}" -u "${ADMIN_USER}" ping >/dev/null 2>&1; then
  "${BREW_BIN}" services start mariadb@10.6 >/dev/null
  sleep 5
fi

"${MYSQL_BIN}" -u "${ADMIN_USER}" < "${DUMP_FILE}"

echo "Restore completed from ${DUMP_FILE}"

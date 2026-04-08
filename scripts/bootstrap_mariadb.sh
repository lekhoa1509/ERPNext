#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MYSQL_BIN="/opt/homebrew/opt/mariadb@10.6/bin/mariadb"
MYSQLADMIN_BIN="/opt/homebrew/opt/mariadb@10.6/bin/mysqladmin"
BREW_BIN="/opt/homebrew/bin/brew"
ADMIN_USER="${BOOTSTRAP_DB_ADMIN_USER:-$(whoami)}"

DB_NAME="${BOOTSTRAP_DB_NAME:-pharma_vn_bootstrap}"
DB_USER="${BOOTSTRAP_DB_USER:-pharma_app}"
DB_PASSWORD="${BOOTSTRAP_DB_PASSWORD:-pharma_app_2026}"

if [[ ! -x "${MYSQL_BIN}" ]]; then
  echo "MariaDB client not found at ${MYSQL_BIN}"
  exit 1
fi

echo "Checking MariaDB service..."
if ! "${MYSQLADMIN_BIN}" -u "${ADMIN_USER}" ping >/dev/null 2>&1; then
  echo "Starting brew service mariadb@10.6..."
  "${BREW_BIN}" services start mariadb@10.6 >/dev/null
  sleep 5
fi

if ! "${MYSQLADMIN_BIN}" -u "${ADMIN_USER}" ping >/dev/null 2>&1; then
  echo "MariaDB service is not reachable."
  exit 1
fi

echo "Creating database and application user..."
"${MYSQL_BIN}" -u "${ADMIN_USER}" <<SQL
CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${DB_USER}'@'localhost';
FLUSH PRIVILEGES;
SQL

echo "Loading schema..."
"${MYSQL_BIN}" -u "${ADMIN_USER}" "${DB_NAME}" < "${ROOT_DIR}/database/sql/10-schema.sql"

echo "Loading Vietnam reference data..."
"${MYSQL_BIN}" -u "${ADMIN_USER}" "${DB_NAME}" < "${ROOT_DIR}/database/sql/20-reference-data.sql"

echo "Loading sample master and transaction data..."
"${MYSQL_BIN}" -u "${ADMIN_USER}" "${DB_NAME}" < "${ROOT_DIR}/database/sql/30-sample-data.sql"

echo "Bootstrap DB is ready."
echo "Database: ${DB_NAME}"
echo "User: ${DB_USER}"
echo "Password: ${DB_PASSWORD}"
echo
echo "Quick summary:"
"${MYSQL_BIN}" -u "${ADMIN_USER}" "${DB_NAME}" -e "
SELECT 'bootstrap_company' AS table_name, COUNT(*) AS rows_count FROM bootstrap_company
UNION ALL
SELECT 'bootstrap_account', COUNT(*) FROM bootstrap_account
UNION ALL
SELECT 'bootstrap_tax_template', COUNT(*) FROM bootstrap_tax_template
UNION ALL
SELECT 'bootstrap_item', COUNT(*) FROM bootstrap_item
UNION ALL
SELECT 'bootstrap_batch', COUNT(*) FROM bootstrap_batch
UNION ALL
SELECT 'bootstrap_customer', COUNT(*) FROM bootstrap_customer
UNION ALL
SELECT 'bootstrap_supplier', COUNT(*) FROM bootstrap_supplier
UNION ALL
SELECT 'bootstrap_sales_order', COUNT(*) FROM bootstrap_sales_order
UNION ALL
SELECT 'bootstrap_purchase_order', COUNT(*) FROM bootstrap_purchase_order;
"

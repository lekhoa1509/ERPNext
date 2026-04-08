#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/deploy/docker-compose.db.yml"

export BOOTSTRAP_DB_NAME="${BOOTSTRAP_DB_NAME:-pharma_vn_bootstrap}"
export BOOTSTRAP_DB_USER="${BOOTSTRAP_DB_USER:-pharma_app}"
export BOOTSTRAP_DB_PASSWORD="${BOOTSTRAP_DB_PASSWORD:-pharma_app_2026}"
export BOOTSTRAP_DB_ROOT_PASSWORD="${BOOTSTRAP_DB_ROOT_PASSWORD:-root_2026_secure}"
export BOOTSTRAP_DB_HOST_PORT="${BOOTSTRAP_DB_HOST_PORT:-3307}"

docker compose -f "${COMPOSE_FILE}" down -v >/dev/null 2>&1 || true
docker compose -f "${COMPOSE_FILE}" up -d

echo "Waiting for pharma-db to become healthy..."
for _ in $(seq 1 60); do
  status="$(docker inspect --format='{{json .State.Health.Status}}' pharma-db 2>/dev/null || true)"
  if [[ "${status}" == "\"healthy\"" ]]; then
    break
  fi
  sleep 2
done

status="$(docker inspect --format='{{json .State.Health.Status}}' pharma-db 2>/dev/null || true)"
if [[ "${status}" != "\"healthy\"" ]]; then
  echo "Container pharma-db is not healthy."
  docker compose -f "${COMPOSE_FILE}" logs --tail=200
  exit 1
fi

echo "Bootstrap Docker DB is ready."
echo "Host: 127.0.0.1"
echo "Port: ${BOOTSTRAP_DB_HOST_PORT}"
echo "Database: ${BOOTSTRAP_DB_NAME}"
echo "User: ${BOOTSTRAP_DB_USER}"
echo "Password: ${BOOTSTRAP_DB_PASSWORD}"
echo
echo "Quick summary:"
docker exec pharma-db mariadb \
  -u"${BOOTSTRAP_DB_USER}" \
  -p"${BOOTSTRAP_DB_PASSWORD}" \
  "${BOOTSTRAP_DB_NAME}" \
  -e "
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


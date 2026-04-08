#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/deploy/docker-compose.erp.yml"
PROJECT_NAME="${ERPNEXT_COMPOSE_PROJECT:-erpnext-pharma}"
SITE_NAME="${ERPNEXT_SITE_NAME:-frontend}"
BACKEND_CONTAINER="${PROJECT_NAME}-backend-1"
SOURCE_FILE="${ROOT_DIR}/apps/pharma_vn/pharma_vn/translations/vi.csv"
TARGET_FILE="/home/frappe/frappe-bench/apps/pharma_vn/pharma_vn/translations/vi.csv"
TEMP_FILE="/tmp/pharma_vn_vi.csv"

if [[ ! -f "${SOURCE_FILE}" ]]; then
  echo "Translation file not found: ${SOURCE_FILE}"
  exit 1
fi

if ! docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" ps backend >/dev/null 2>&1; then
  echo "Backend service is not available."
  exit 1
fi

docker cp "${SOURCE_FILE}" "${BACKEND_CONTAINER}:${TEMP_FILE}"

docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" exec -T --user root backend \
  bash -lc "install -o frappe -g frappe -m 0644 \"${TEMP_FILE}\" \"${TARGET_FILE}\" && rm -f \"${TEMP_FILE}\""

docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" exec -T backend \
  bash -lc "bench --site \"${SITE_NAME}\" clear-cache >/dev/null 2>&1 || true"

echo "Vietnamese translations synced to ${BACKEND_CONTAINER} for site ${SITE_NAME}."

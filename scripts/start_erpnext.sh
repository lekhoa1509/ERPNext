#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/deploy/docker-compose.erp.yml"
PROJECT_NAME="${ERPNEXT_COMPOSE_PROJECT:-erpnext-pharma}"

export ERPNEXT_VERSION="${ERPNEXT_VERSION:-v16.12.0}"
export ERPNEXT_SITE_NAME="${ERPNEXT_SITE_NAME:-frontend}"
export ERPNEXT_ADMIN_PASSWORD="${ERPNEXT_ADMIN_PASSWORD:-admin}"
export ERPNEXT_DB_ROOT_PASSWORD="${ERPNEXT_DB_ROOT_PASSWORD:-admin}"
export ERPNEXT_HTTP_PORT="${ERPNEXT_HTTP_PORT:-8080}"

docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" up -d --build

echo "Waiting for create-site job to finish..."
CREATE_SITE_ID="$(docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" ps -q create-site)"
if [[ -n "${CREATE_SITE_ID}" ]]; then
  for _ in $(seq 1 90); do
    STATUS="$(docker inspect --format='{{.State.Status}}' "${CREATE_SITE_ID}")"
    if [[ "${STATUS}" == "exited" ]]; then
      EXIT_CODE="$(docker inspect --format='{{.State.ExitCode}}' "${CREATE_SITE_ID}")"
      if [[ "${EXIT_CODE}" != "0" ]]; then
        echo "create-site failed with exit code ${EXIT_CODE}"
        docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" logs --tail=200 create-site
        exit 1
      fi
      break
    fi
    sleep 5
  done
fi

echo "Waiting for frontend to answer on http://127.0.0.1:${ERPNEXT_HTTP_PORT} ..."
for _ in $(seq 1 90); do
  if curl -fsS "http://127.0.0.1:${ERPNEXT_HTTP_PORT}" >/dev/null 2>&1; then
    docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" exec -T backend \
      bash -lc "mkdir -p /home/frappe/frappe-bench/sites/assets; \
      ln -sfn /home/frappe/frappe-bench/apps/pharma_vn/pharma_vn/public /home/frappe/frappe-bench/sites/assets/pharma_vn; \
      bench --site \"${ERPNEXT_SITE_NAME}\" clear-cache >/dev/null 2>&1 || true; \
      bench --site \"${ERPNEXT_SITE_NAME}\" enable-scheduler >/dev/null 2>&1 || true"
    "${ROOT_DIR}/scripts/sync_vi_translations.sh"
    echo "ERPNext is up."
    echo "URL: http://127.0.0.1:${ERPNEXT_HTTP_PORT}"
    echo "Site: ${ERPNEXT_SITE_NAME}"
    echo "User: Administrator"
    echo "Password: ${ERPNEXT_ADMIN_PASSWORD}"
    exit 0
  fi
  sleep 5
done

echo "Frontend did not become ready in time."
docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" logs --tail=200 frontend create-site backend
exit 1

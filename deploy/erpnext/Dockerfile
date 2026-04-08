ARG ERPNEXT_VERSION=v16.12.0
FROM frappe/erpnext:${ERPNEXT_VERSION}

USER root

COPY apps/pharma_vn /home/frappe/frappe-bench/apps/pharma_vn
RUN chown -R frappe:frappe /home/frappe/frappe-bench/apps/pharma_vn

USER frappe

RUN /home/frappe/frappe-bench/env/bin/pip install --no-cache-dir -e /home/frappe/frappe-bench/apps/pharma_vn

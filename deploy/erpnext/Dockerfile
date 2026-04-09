ARG ERPNEXT_VERSION=v16.12.0
ARG HRMS_VERSION=version-16
FROM frappe/erpnext:${ERPNEXT_VERSION}
ARG HRMS_VERSION

USER root

RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

USER frappe

RUN if [ ! -d /home/frappe/frappe-bench/apps/hrms ]; then \
      bench get-app --skip-assets --branch ${HRMS_VERSION} hrms https://github.com/frappe/hrms.git; \
    fi

USER root

COPY apps/pharma_vn /home/frappe/frappe-bench/apps/pharma_vn
RUN chown -R frappe:frappe /home/frappe/frappe-bench/apps/pharma_vn

USER frappe

RUN /home/frappe/frappe-bench/env/bin/pip install --no-cache-dir -e /home/frappe/frappe-bench/apps/hrms
RUN /home/frappe/frappe-bench/env/bin/pip install --no-cache-dir -e /home/frappe/frappe-bench/apps/pharma_vn

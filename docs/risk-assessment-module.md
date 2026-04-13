# Customer Risk Assessment Module

Module nay bo sung quy trinh danh gia rui ro khach hang cho ERPNext/Frappe, ket hop:

- `Customer Risk Profile` DocType de luu ket qua check
- API proxy trong `pharma_vn.api.risk`
- React widget nhung ngay trong form `Customer`
- Rule chan submit `Sales Order` neu khach hang dang `HIGH` risk

## File chinh

- Backend service: `apps/pharma_vn/pharma_vn/risk_assessment/service.py`
- Backend API: `apps/pharma_vn/pharma_vn/api/risk.py`
- DocType: `apps/pharma_vn/pharma_vn/risk_assessment/doctype/customer_risk_profile/`
- Customer integration: `apps/pharma_vn/pharma_vn/public/js/customer.js`
- React widget source: `apps/pharma_vn/frontend/risk_dashboard/src/`
- React widget bundle: `apps/pharma_vn/pharma_vn/public/js/customer_risk_widget.bundle.js`

## Install vao bench ERPNext

1. Lay app vao bench:

```bash
bench get-app /path/to/this/repo/apps/pharma_vn
```

2. Cai package frontend neu can build lai widget:

```bash
cd apps/pharma_vn
npm install
npm run build:risk-widget
cd ../..
```

3. Cai app vao site:

```bash
bench --site your-site install-app pharma_vn
```

4. Chay migrate de tao DocType, custom fields va hooks:

```bash
bench --site your-site migrate
bench build --app pharma_vn
```

5. Xoa cache neu dang nang cap tren site da chay:

```bash
bench --site your-site clear-cache
```

## Cau hinh backend

Co the dat trong `site_config.json`, `common_site_config.json` hoac env vars.

### Risk Engine

- `risk_engine_url` hoac `PHARMA_VN_RISK_ENGINE_URL`
  - mac dinh: `http://localhost:5000/api/risk/check`
- `risk_engine_api_key` hoac `PHARMA_VN_RISK_ENGINE_API_KEY`
- `risk_engine_timeout` hoac `PHARMA_VN_RISK_ENGINE_TIMEOUT`

### Tax Business API / XInvoice

- `tax_business_api_url` hoac `PHARMA_VN_TAX_BUSINESS_API_URL`
  - ten config uu tien de lay thong tin doanh nghiep tu tax API
  - ho tro URL co placeholder `{tax_code}`
  - mac dinh: `https://api.xinvoice.vn/gdt-api/tax-payer/{tax_code}`
- `tax_business_api_method` hoac `PHARMA_VN_TAX_BUSINESS_API_METHOD`
  - mac dinh: `GET`
- `tax_business_api_key` hoac `PHARMA_VN_TAX_BUSINESS_API_KEY`
- `tax_business_api_client_id` hoac `PHARMA_VN_TAX_BUSINESS_API_CLIENT_ID`
- `tax_business_api_timeout` hoac `PHARMA_VN_TAX_BUSINESS_API_TIMEOUT`
- `tax_business_api_source` hoac `PHARMA_VN_TAX_BUSINESS_API_SOURCE`
  - mac dinh: `XInvoice Tax API`

API XInvoice hien tra cac truong nhu:

- `orgType`
- `taxID`
- `name`
- `address`
- `taxDepartment`
- `status`
- `updatedAt`

- Tuong thich nguoc voi config cu:
  - `vietqr_business_api_url` hoac `PHARMA_VN_VIETQR_BUSINESS_API_URL`
  - ho tro URL co placeholder `{tax_code}`
  - vi du: `https://your-vietqr-proxy/api/business/{tax_code}`
- `vietqr_business_api_method` hoac `PHARMA_VN_VIETQR_BUSINESS_API_METHOD`
  - `GET` hoac `POST`
- `vietqr_business_api_key` hoac `PHARMA_VN_VIETQR_BUSINESS_API_KEY`
- `vietqr_business_api_timeout` hoac `PHARMA_VN_VIETQR_BUSINESS_API_TIMEOUT`

### Hanh vi module

- `risk_cache_ttl_minutes` hoac `PHARMA_VN_RISK_CACHE_TTL_MINUTES`
  - mac dinh: `1440`
- `risk_block_sales_order_on_high` hoac `PHARMA_VN_RISK_BLOCK_SALES_ORDER_ON_HIGH`
  - mac dinh: `1`

## Cach su dung

1. Mo `Customer`
2. Dien `Tax ID`
3. Bam `Check Risk`
4. Widget React se hien:
   - Risk Score
   - Risk Level
   - Reasons
   - Business Profile tu XInvoice / tax API
   - Lich su check gan day

Ket qua moi se duoc luu vao `Customer Risk Profile`.

Neu API tax tra ve `company_name` va `Customer.customer_name` dang trong, module se tu sync ten doanh nghiep ve `Customer`.

## Mock local de test

Chay mock engine + mock tax API:

```bash
cd /Users/lekhoa.lekhoa2gmail.com/Documents/ERPNext
python3 scripts/mock_risk_engine.py --host 127.0.0.1 --port 5051
```

Config site `frontend` trong Docker voi XInvoice live API:

```bash
docker compose -p erpnext-pharma -f deploy/docker-compose.erp.yml exec -T backend \
  bash -lc 'bench --site frontend set-config tax_business_api_url https://api.xinvoice.vn/gdt-api/tax-payer/{tax_code} && \
  bench --site frontend set-config tax_business_api_method GET && \
  bench --site frontend set-config tax_business_api_source "XInvoice Tax API" && \
  bench --site frontend clear-cache'
```

Neu sau nay can them header:

```bash
docker compose -p erpnext-pharma -f deploy/docker-compose.erp.yml exec -T backend \
  bash -lc 'bench --site frontend set-config tax_business_api_client_id YOUR_CLIENT_ID && \
  bench --site frontend set-config tax_business_api_key YOUR_API_KEY && \
  bench --site frontend clear-cache'
```

Mock local van giu lai de test:

```bash
docker compose -p erpnext-pharma -f deploy/docker-compose.erp.yml exec -T backend \
  bash -lc 'bench --site frontend set-config risk_engine_url http://host.docker.internal:5051/api/risk/check && \
  bench --site frontend set-config tax_business_api_url http://host.docker.internal:5051/api/tax/business/{tax_code} && \
  bench --site frontend set-config tax_business_api_source "Mock Tax Business API" && \
  bench --site frontend clear-cache'
```

Tax code de test:

- `HIGH001` -> doanh nghiep + `HIGH`
- `WARN001` -> doanh nghiep + `WARNING`
- `SAFE001` -> doanh nghiep + `SAFE`

## API dung tu frontend

- Check / refresh:

```python
frappe.call({
    method: "pharma_vn.api.risk.check",
    args: {
        customer: frm.doc.name,
        tax_code: frm.doc.tax_id,
        force_refresh: 0,
    },
});
```

- Lay ket qua gan nhat:

```python
frappe.call({
    method: "pharma_vn.api.risk.get_customer_risk",
    args: {
        customer: frm.doc.name,
    },
});
```

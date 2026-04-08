# ERPNext Pharma Vietnam Blueprint

Blueprint trien khai ERPNext cho doanh nghiep duoc tai Viet Nam, bao gom:

- Tai lieu solution design va quy trinh nghiep vu end-to-end.
- Skeleton custom app Frappe/ERPNext `pharma_vn`.
- Khung API, automation, custom DocType va deployment tham khao.

## Cau truc repo

- `docs/solution-design.md`: tai lieu tong the.
- `docs/processes/`: quy trinh chi tiet theo module.
- `docs/processes/erpnext-user-sop.md`: SOP thao tac tren phan mem cho ban hang, mua hang, nhap kho, xuat kho, chuyen kho.
- `docs/processes/sales-order-byd-mapping.md`: mapping form Sales Order theo SAP ByD.
- `docs/architecture/`: tich hop, bao mat, bao cao, deployment.
- `docs/templates/naming-convention.md`: quy uoc dat ten va series.
- `apps/pharma_vn/`: custom app ERPNext/Frappe.
- `database/`: bootstrap MariaDB schema va seed data cho Viet Nam.
- `deploy/docker-compose.yml`: stack tham khao de len moi truong.

## Doi tuong doanh nghiep

- Nganh: Duoc pham, thuc pham bao ve suc khoe.
- Quy mo: 200-500 nhan su.
- Thi truong: Viet Nam.
- Mo hinh: Hybrid B2B/B2C.

## Pham vi custom app `pharma_vn`

- Batch release truoc khi ban.
- Quan ly nhiet do kho va cold-chain.
- Recall batch va truy vet nguoc/xuoi.
- API tich hop website, payment gateway, WMS/handheld, CRM/DMS.
- Custom fields cho Item, Batch, Customer, Supplier, Sales/Purchase docs.

## Cach su dung

1. Doc tai lieu trong `docs/`.
2. Dua app `apps/pharma_vn` vao bench ERPNext thuc te.
3. Cai app len site:

```bash
bench --site your-site install-app pharma_vn
```

4. Cau hinh API keys, scheduler, warehouse structure, workflow va user permissions theo tai lieu.

## Chay ERPNext bang Docker

Khoi dong stack ERPNext local:

```bash
./scripts/start_erpnext.sh
```

Truy cap:

- URL: `http://127.0.0.1:8080`
- Site: `frontend`
- User: `Administrator`
- Password: `admin`

Dung stack:

```bash
./scripts/stop_erpnext.sh
```

Xem log:

```bash
./scripts/logs_erpnext.sh
```

## Seed du lieu demo trong site ERPNext

Site `frontend` co the duoc seed bang bootstrap cho doanh nghiep duoc Viet Nam:

```bash
docker compose -p erpnext-pharma -f deploy/docker-compose.erp.yml exec backend \
  bash -lc 'bench --site frontend execute pharma_vn.setup.bootstrap_demo.bootstrap_vietnam_demo'
```

Bootstrap tao:

- `1` company demo `Viet An Pharma JSC`
- kho theo mo hinh quarantine/released/distribution
- tax templates `VAT 5%`, `VAT 8%`, `VAT 10%` cho sales va purchase
- `3` item demo quan ly batch/expiry
- `2` customer, `2` supplier, `3` batch demo
- contact, bill-to, ship-to cho khach hang duoc
- `1` Sales Order mau B2B de UAT header + approval workflow

## Bootstrap DB local

1. Cai MariaDB 10.6 bang Homebrew.
2. Chay script:

```bash
./scripts/bootstrap_mariadb.sh
```

3. Truy van nhanh:

```bash
./scripts/query_bootstrap_db.sh "SELECT * FROM bootstrap_tax_template;"
```

Neu chay bang Docker:

```bash
docker context use default
./scripts/bootstrap_docker_db.sh
./scripts/query_docker_db.sh "SELECT * FROM bootstrap_tax_template;"
```

Docker DB hien map ra host port `3307` de tranh xung dot voi MariaDB local dang co tren `3306`.

DB bootstrap mac dinh:

- Database: `pharma_vn_bootstrap`
- User: `pharma_app`
- Password: `pharma_app_2026`

## Ghi chu

- Repo nay la skeleton de khoi dong du an, chua phai bench ERPNext day du.
- Toan bo custom nen duoc dua vao app rieng, khong sua truc tiep core ERPNext.

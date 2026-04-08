# Bootstrap Database

Thu muc nay chua bo script de tao MariaDB local cho du an ERPNext duoc Viet Nam.

## Muc dich

- Tao DB local de giu:
  - danh muc cong ty
  - chart of accounts seed
  - tax templates theo quy dinh Viet Nam
  - danh muc item, kho, customer, supplier
  - mot vai giao dich mau
- Dung lam nguon du lieu khoi tao cho ERPNext site sau nay.

## Ghi chu quan trong

- Day la `bootstrap database`, khong phai schema core cua ERPNext/Frappe.
- Khi co bench ERPNext, du lieu seed trong DB nay se duoc map vao Company, Account, Item Group, Item, Warehouse, Customer, Supplier va tax masters cua ERPNext.
- Tax va chart of accounts duoc seed theo boi canh Viet Nam nam 2026.

## Nguon tham chieu phap ly

- Luat so 48/2024/QH15 ve thue GTGT, hieu luc tu `2025-07-01`.
- Luat so 149/2025/QH15 sua doi, bo sung mot so dieu cua Luat Thue GTGT, hieu luc tu `2026-01-01`.
- Nghi quyet so 204/2025/QH15 ve giam 2% thue GTGT, hieu luc tu `2025-07-01` den het `2026-12-31`.
- Nghi dinh so 174/2025/ND-CP huong dan chinh sach giam thue GTGT theo Nghi quyet 204/2025/QH15.
- Thong tu so 99/2025/TT-BTC huong dan che do ke toan doanh nghiep, hieu luc tu `2026-01-01`.

## Dung nhanh

```bash
./scripts/bootstrap_mariadb.sh
```

## Docker mode

```bash
docker context use default
./scripts/bootstrap_docker_db.sh
```

Mac dinh Docker DB listen o host port `3307` de tranh xung dot voi MariaDB local.

Sau khi chay xong, DB mac dinh:

- Database: `pharma_vn_bootstrap`
- User: `pharma_app`
- Password: `pharma_app_2026`

## Bang du lieu chinh

- `bootstrap_company`
- `bootstrap_account`
- `bootstrap_tax_template`
- `bootstrap_item_group`
- `bootstrap_warehouse`
- `bootstrap_supplier`
- `bootstrap_customer`
- `bootstrap_item`
- `bootstrap_batch`
- `bootstrap_sales_order`
- `bootstrap_sales_order_item`
- `bootstrap_purchase_order`
- `bootstrap_purchase_order_item`

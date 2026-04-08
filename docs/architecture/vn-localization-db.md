# Vietnam Localization for Bootstrap DB

## 1. Muc tieu

- Tao bo seed database co the dung ngay cho du an ERPNext duoc.
- Bao gom chart of accounts, tax templates va danh muc mau cho doanh nghiep Viet Nam.

## 2. Tax logic seed

- `VAT-OUT-5` / `VAT-IN-5`
  - dung cho thuoc chua benh, thuoc phong benh, duoc chat nguyen lieu san xuat thuoc
  - implementation mapping nay duoc giu theo logic cua Luat 48/2024/QH15 va boi canh cap nhat 2026
- `VAT-OUT-8` / `VAT-IN-8`
  - dung cho nhom hang hoa dich vu du dieu kien giam 2% tu 10% xuong 8%
  - chi co hieu luc trong giai doan uu dai
- `VAT-OUT-10` / `VAT-IN-10`
  - dung cho nhom hang hoa dich vu ap dung muc thong thuong
- `VAT-OUT-0`
  - dung cho xuat khau, zero-rated khi du dieu kien

## 3. Tax accounts seed

- `1331`: thue GTGT dau vao duoc khau tru cua hang hoa dich vu
- `1332`: thue GTGT dau vao duoc khau tru cua tai san co dinh
- `33311`: thue GTGT dau ra phai nop
- `33312`: thue GTGT hang nhap khau
- `3334`: thue thu nhap doanh nghiep
- `3335`: thue thu nhap ca nhan

## 4. Canh bao nghiep vu

- `8%` la template tam thoi theo chinh sach giam thue, khong tu dong gan cho moi item.
- Item duoc pham mac dinh nen map `5%` neu thuoc pham vi thuoc chua benh/phong benh hoac duoc chat nguyen lieu theo luat.
- Supplements, packaging, services va cac nhom khac can duoc finance/tax review truoc khi gan template.
- Luat 149/2025/QH15 co hieu luc tu `2026-01-01`, do do truoc khi go-live prod can doi chieu them voi accountant va tax advisor.

## 5. Cach map vao ERPNext sau nay

- `bootstrap_account` -> `Account`
- `bootstrap_tax_template` -> `Sales Taxes and Charges Template` / `Purchase Taxes and Charges Template`
- `bootstrap_item_group` -> `Item Group`
- `bootstrap_item` -> `Item`
- `bootstrap_warehouse` -> `Warehouse`
- `bootstrap_customer` -> `Customer`
- `bootstrap_supplier` -> `Supplier`
- `bootstrap_batch` -> `Batch`

# Accounting Flow

## 1. Muc tieu

- Ghi nhan day du doanh thu, gia von, cong no, VAT, chi phi va tai san.
- Dam bao doi chieu du lieu voi kho, mua hang, ban hang va san xuat.

## 2. Accounts receivable

1. `Sales Invoice` duoc tao tu `Delivery Note` hoac `Sales Order`.
2. He thong sinh `GL Entry`.
3. Dong bo hoa don dien tu neu ap dung.
4. Theo doi `Payment Terms`.
5. Thu tien qua:
   - chuyen khoan
   - gateway
   - COD
6. Tao `Payment Entry`.
7. Doi chieu sao ke ngan hang.

## 3. Accounts payable

1. `Purchase Invoice` tao tu `Purchase Receipt` hoac PO.
2. Kiem tra 3-way match:
   - PO
   - GRN/Purchase Receipt
   - Invoice
3. Sinh `GL Entry`.
4. Lap lich thanh toan theo due date.
5. Tao `Payment Entry`.

## 4. Inventory accounting

- Moi nghiep vu kho sinh anh huong gia tri ton kho.
- Su dung perpetual inventory.
- Landed cost duoc phan bo vao batch/item nhap.
- Dieu chinh kho phai co workflow va audit trail.

## 5. Manufacturing accounting

- Issue nguyen lieu vao Work Order.
- Ghi nhan WIP.
- Hoan thanh thanh pham -> ket chuyen gia tri tu WIP sang FG.
- Theo doi sai lech BOM/yield.

## 6. Month-end close checklist

1. Khoa ky tu ngay cat so.
2. Hoan tat QC release cho lo da nhap/san xuat.
3. Doi chieu ton kho so sach va thuc te.
4. Doi chieu AR/AP.
5. Chay khau hao va phan bo.
6. Tinh gia von neu co dieu chinh.
7. Chot bao cao VAT.
8. Chay PnL, Balance Sheet, Cash Flow.

## 7. Bao cao bat buoc

- AR aging
- AP aging
- doanh thu theo kenh
- gross margin theo nhom san pham
- VAT dau vao/dau ra
- ton kho va near-expiry

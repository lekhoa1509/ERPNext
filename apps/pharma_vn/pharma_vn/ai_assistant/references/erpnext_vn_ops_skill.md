# ERPNext Vietnam Operations Skill

Su dung kien thuc nay khi user hoi quy trinh ERP, hoa don, kho, ton kho, VAT, e-invoice, nghi dinh, thong tu, hoac cach thao tac tren ERPNext.

## Dieu huong intent

- Neu user muon tao du lieu hay thuc hien hanh dong co san: dung intent phu hop nhu `create_customer`, `create_sales_order_draft`, `create_auto_email_report`, `stock_lookup`.
- Neu user hoi "quy trinh nao dung", "nen tao chung tu gi truoc", "cach kiem tra ton kho", "hoa don di theo luong nao", "VAT/ap dung theo nghiep vu nao", hoac hoi ve `nghi dinh`, `thong tu`, `luat`: dung `help`.
- Neu user hoi ton kho cho mot item cu the, co hoac khong co kho cu the: uu tien `stock_lookup`.

## Quy trinh ban hang

- Luong chuan: `Quotation -> Sales Order -> Delivery Note -> Sales Invoice -> Payment Entry`.
- Neu ban nhanh co the bo qua `Quotation`, nhung van uu tien `Sales Order -> Delivery Note -> Sales Invoice`.
- Xuat kho chi nen lay tu kho `Released` hoac kho ban hang da duoc phep xuat.
- Batch nen duoc chon theo FEFO va phai con ton thuc te trong dung warehouse.
- Neu user hoi "xuat kho cho khach" thi nhac `Delivery Note`; neu hoi "ghi nhan doanh thu/hoa don" thi nhac `Sales Invoice`.

## Quy trinh mua hang

- Luong chuan: `Request for Quotation -> Supplier Quotation -> Purchase Order -> Purchase Receipt -> Purchase Invoice -> Payment Entry`.
- Khi hang ve, neu can QA thi nhap `Quarantine` truoc.
- Sau kiem nghiem dat, tao `PH Batch Release` neu ap dung roi chuyen kho sang `Released`.
- Neu khong dat: dua vao `Rejected` hoac xu ly `Purchase Return`.
- Neu co phi van chuyen, bao hiem, thue nhap khau: nhac `Landed Cost Voucher`.

## Nghiep vu kho

- Xuat kho noi bo khong ban hang: `Stock Entry` voi purpose `Material Issue`.
- Nhap kho noi bo khong qua PO: `Stock Entry` voi purpose `Material Receipt`.
- Chuyen kho: `Stock Entry` voi purpose `Material Transfer`.
- Chuyen `Quarantine -> Released` cung la `Material Transfer`.
- Kho `Quarantine` va `Rejected` khong duoc xuat ban.

## Hoa don va ke toan

- `Sales Invoice` thuong tao tu `Delivery Note` hoac `Sales Order`.
- `Purchase Invoice` thuong tao tu `Purchase Receipt` hoac `Purchase Order`.
- E-invoice thuong theo sau khi `Sales Invoice` da duoc submit va he thong tich hop da phat hanh so hoa don.
- Ke toan can doi chieu 3-way match cho mua hang: `PO`, `Purchase Receipt`, `Purchase Invoice`.
- Neu user hoi "hoa don ban hang di sau chung tu nao" thi cau tra loi mac dinh la sau `Delivery Note`, tru khi doanh nghiep dung luong bill truoc giao.

## Cach kiem tra ton kho

- Kiem tra nhanh trong assistant: dung `stock_lookup` theo `item` va co the kem `warehouse`.
- Trong ERPNext, goi y cac cach kiem tra:
  - `Stock Balance` de xem ton theo item/kho.
  - `Warehouse Wise Stock Balance` de xem ton theo tung kho.
  - `Batch-wise Balance History` neu can theo doi lo/han dung.
  - `Stock Ledger` neu can truy vet phat sinh tang giam.
- Neu co quan ly vi tri, co the xem them `WH Cell Stock` de biet item dang nam o cell nao, so luong bao nhieu, batch nao.
- Khi tra loi, nhac user xac dinh ro `item code`, `warehouse`, `batch`, va neu can thi xem them ton kha dung, near-expiry, hoac ton trong `Released` thay vi `Quarantine`.

## Huong dan tra loi phap ly Viet Nam

- Chi tra loi o muc dinh huong nghiep vu, khong khang dinh day la tu van phap ly hay tu van thue.
- Khong tu y che so dieu, nghi dinh, thong tu, cong van, ngay hieu luc neu user khong cung cap hoac he thong khong co nguon xac minh.
- Neu user hoi ve `nghi dinh`, `thong tu`, `luat`, `hoa don dien tu`, `VAT`, `thue`, can tra loi theo mau:
  - neu cau hoi la nghiep vu: giai thich logic van hanh tren ERPNext;
  - kem canh bao phai doi chieu van ban moi nhat va xac nhan voi accountant/tax advisor truoc khi ap dung.
- Co the nhac boi canh repo hien co cac muc VAT `5%`, `8%`, `10%`, `0%`, nhung viec gan thue cho item/phat sinh cu the van can finance-tax review.

## Van phong cach

- Tra loi ngan, ro, uu tien checklist thao tac.
- Neu user hoi "nen dung chung tu nao" thi tra loi theo thu tu chung tu va dieu kien dung.
- Neu user hoi "tai sao khong xuat duoc" thi goi y kiem tra: warehouse, batch, ton thuc te, trang thai released, han dung.

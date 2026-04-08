# Purchase Flow

## 1. Muc tieu

- Mua hang dung nha cung cap, dung gia, dung lead time.
- Dam bao nguyen lieu/thanh pham mua vao duoc QA kiem soat truoc khi dua vao su dung.

## 2. Quy trinh mua hang

1. Nhu cau mua hang phat sinh tu:
   - `Reorder Level`
   - `Production Plan`
   - `Material Request`
   - yeu cau mua hang thu cong
2. Bo phan mua hang tong hop nhu cau.
3. Kiem tra nha cung cap:
   - da approved hay chua
   - GMP/GDP con han khong
   - lich su chat luong
4. Tao `Request for Quotation`.
5. Nhan `Supplier Quotation`.
6. So sanh nha cung cap theo:
   - gia
   - lead time
   - payment term
   - COA/CO/CQ
7. Tao `Purchase Order`.
8. `Purchase Order` vao workflow approval theo gia tri.
9. Hang ve kho:
   - tao `Purchase Receipt`
   - nhap vao kho `Quarantine`
10. He thong tu dong sinh `Quality Inspection` neu item co `qa_required`.
11. QA thuc hien kiem nghiem:
   - doi chieu chung tu
   - ngoai quan
   - batch/lot
   - han dung
   - chi tieu chat luong
12. Neu dat:
   - tao `PH Batch Release`
   - chuyen kho sang `Released`
13. Neu khong dat:
   - chuyen kho `Rejected`
   - hoac `Purchase Return`
14. Ke toan nhan `Purchase Invoice`.
15. Tinh `Landed Cost Voucher` neu co cuoc/bao hiem/thue.
16. Thanh toan qua `Payment Entry`.

## 3. Quy trinh mua nhap khau

1. Tao PO voi `incoterm`, ETA, cang nhap, agent.
2. Theo doi bo chung tu: invoice, packing list, CO, CQ, COA.
3. Hang cap cang -> kho ngoai quan/warehouse.
4. Nhap `Purchase Receipt`.
5. Tinh chi phi nhap khau qua landed cost.
6. QA release truoc khi dua vao ban/san xuat.

## 4. Business rules

- Supplier moi phai qua danh gia va phe duyet.
- Item co `qa_required = 1` khong duoc dua thang vao kho su dung.
- Batch nhap co han dung duoi nguong toi thieu phai canh bao va co workflow.
- Mua hang chien luoc/nhap khau can attach file chung tu tren ERP.

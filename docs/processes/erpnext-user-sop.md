# ERPNext User SOP

## 1. Muc tieu

- Chuan hoa cach thao tac tren ERPNext cho doanh nghiep duoc.
- Biet ro chung tu nao duoc tao truoc, chung tu nao duoc tao sau.
- Giam sai sot khi nhap kho, xuat kho, chon batch va chuyen kho noi bo.

## 2. Pham vi ap dung

- Site: `frontend`
- Company: `Viet An Pharma JSC`
- Nhom nghiep vu:
  - ban hang
  - mua hang
  - nhap kho
  - xuat kho
  - chuyen kho giua cac kho
  - QA release truoc khi dua hang vao kho su dung

## 3. Kho va logic van hanh mac dinh

- `FG Quarantine - VAP`: kho thanh pham cho QA kiem tra
- `FG Released - VAP`: kho thanh pham da duoc release, duoc phep xuat
- `HCM Sellable - VAP`: kho ban hang HCM
- `HN Sellable - VAP`: kho ban hang HN
- `RM Quarantine - VAP`: kho nguyen lieu cho QA
- `RM Released - VAP`: kho nguyen lieu da duoc phep dua vao san xuat
- `Work In Progress - VAP`: kho dang san xuat, khong phai kho giao khach mac dinh

## 4. Quy tac chon chung tu

- Ban cho khach hang: dung `Sales Order` -> `Delivery Note` -> `Sales Invoice`
- Mua tu nha cung cap: dung `Purchase Order` -> `Purchase Receipt` -> `Purchase Invoice`
- Xuat kho noi bo khong lien quan khach hang: dung `Stock Entry` voi purpose `Material Issue`
- Nhap kho noi bo khong lien quan PO: dung `Stock Entry` voi purpose `Material Receipt`
- Chuyen giua 2 kho: dung `Stock Entry` voi purpose `Material Transfer`
- Chuyen tu `Quarantine` sang `Released`: dung `Stock Entry` voi purpose `Material Transfer`

## 5. Quy trinh ban hang tren phan mem

## 5.1 Truong hop day du tu bao gia den thu tien

### Dau vao

- Khach hang da ton tai
- Item da co gia ban
- Ton kho da co trong `FG Released - VAP` hoac kho ban hang

### Buoc 1: Tao bao gia

1. Vao `Selling > Quotation`.
2. Bam `New`.
3. Nhap:
   - `Customer`
   - `Quotation To = Customer`
   - ngay bao gia
   - item, so luong, don gia
4. Bam `Save`.
5. Neu can, bam `Submit`.

### Buoc 2: Tao Sales Order

1. Tu `Quotation`, bam `Create > Sales Order`.
2. Hoac vao truc tiep `Selling > Sales Order` va bam `New`.
3. Nhap phan dau chung tu:
   - `Customer`
   - `Transaction Date`
   - `Delivery Date`
   - `Taxes and Charges`
   - dia chi giao hang
4. Nhap dong hang:
   - `Item Code`
   - `Qty`
   - `Warehouse`
5. Bam `Save`.
6. Neu co workflow, chuyen sang trang thai duyet.
7. Sau khi duyet, bam `Submit`.

### Buoc 3: Tao Delivery Note

1. Mo `Sales Order`.
2. Bam `Create > Delivery`.
3. He thong tao `Delivery Note`.
4. Kiem tra:
   - `Customer`
   - `Posting Date`
   - `Warehouse`
   - `Qty`

### Buoc 4: Chon lo hoac serial tren Delivery Note

1. Tai dong hang, bam `Pick Serial / Batch No`.
2. He thong mo dialog chon lo/serial.
3. Trong dialog:
   - chon lo ton tai theo FEFO
   - co the doi `Warehouse` neu can lay hang tu kho khac
   - co the bam `Mo picker day du` neu can tach nhieu lo
   - co the bam `Tao lo moi` hoac `Tao serial moi`
4. Bam `Ap dung`.
5. Kiem tra lai tren dong hang:
   - `Batch No`
   - `Warehouse`
   - `Actual Batch Qty`

### Luu y quan trong

- Khi xuat kho, uu tien chon lo da co ton thuc te.
- `Tao lo moi` chi tao master `Batch`, khong tu sinh ton kho.
- Muon xuat duoc, lo phai co ton kho trong warehouse dang chon.

### Buoc 5: Xac nhan xuat kho

1. Sau khi da gan lo, bam `Save`.
2. Kiem tra tong so luong va kho xuat.
3. Bam `Submit`.
4. Ket qua:
   - ton kho giam
   - batch traceability duoc luu

### Buoc 6: Tao Sales Invoice

1. Tu `Delivery Note`, bam `Create > Sales Invoice`.
2. Kiem tra:
   - gia ban
   - VAT
   - doanh thu
3. Bam `Save`.
4. Bam `Submit`.

### Buoc 7: Thu tien

1. Tu `Sales Invoice`, bam `Create > Payment`.
2. Nhap:
   - `Mode of Payment`
   - `Paid Amount`
   - `Reference No`
3. Bam `Submit`.

### Dau ra

- `Sales Order`
- `Delivery Note`
- `Sales Invoice`
- `Payment Entry`

## 5.2 Truong hop tao nhanh don ban khong qua bao gia

1. Vao `Selling > Sales Order`.
2. Bam `New`.
3. Chon `Customer`.
4. Chon item, so luong, kho xuat.
5. `Save` -> `Submit`.
6. Bam `Create > Delivery`.
7. Chon batch.
8. `Submit Delivery Note`.
9. Bam `Create > Sales Invoice`.
10. `Submit Sales Invoice`.
11. Tao `Payment Entry` neu da thu tien.

## 6. Quy trinh mua hang tren phan mem

## 6.1 Mua hang day du

### Dau vao

- Nha cung cap da ton tai
- Item da ton tai
- Da biet kho nhap

### Buoc 1: Tao Purchase Order

1. Vao `Buying > Purchase Order`.
2. Bam `New`.
3. Nhap:
   - `Supplier`
   - `Schedule Date`
   - `Set Warehouse`
   - `Taxes and Charges`
4. Nhap danh sach item:
   - `Item Code`
   - `Qty`
   - `Rate`
5. Bam `Save`.
6. Neu co workflow, gui duyet.
7. Sau khi duyet, `Submit`.

### Buoc 2: Tao Purchase Receipt

1. Mo `Purchase Order`.
2. Bam `Create > Purchase Receipt`.
3. Kiem tra:
   - `Supplier`
   - `Posting Date`
   - `Warehouse`
   - `Qty`
4. Neu hang duoc can QA, nhap vao kho `FG Quarantine - VAP` hoac `RM Quarantine - VAP`.

### Buoc 3: Gan batch khi nhap hang

1. Tai dong hang trong `Purchase Receipt`, chon:
   - `Batch No` neu nha cung cap da co lo
   - hoac de he thong tao batch noi bo
2. Co the nhap them `Supplier Batch No` neu doanh nghiep can doi chieu lo NCC.
3. `Save`.
4. `Submit`.

### Ket qua sau submit

- He thong sinh ton kho
- He thong tao `Serial and Batch Bundle` cho dong hang co batch/serial
- Co the sinh chung tu `PH Batch Release` cho QA neu item can kiem soat

### Buoc 4: QA release

1. QA mo `PH Batch Release`.
2. Kiem tra:
   - batch
   - item
   - quyet dinh release/hold/reject
3. Neu dat, release lo.
4. Sau release, chuyen hang sang kho `Released`.

### Buoc 5: Tao Purchase Invoice

1. Mo `Purchase Receipt`.
2. Bam `Create > Purchase Invoice`.
3. Kiem tra so luong, VAT, gia mua.
4. `Save` -> `Submit`.

### Buoc 6: Thanh toan nha cung cap

1. Tu `Purchase Invoice`, bam `Create > Payment`.
2. Nhap:
   - `Mode of Payment`
   - `Paid Amount`
   - so chung tu thanh toan
3. `Submit`.

## 7. Quy trinh nhap kho

## 7.1 Nhap kho tu nha cung cap

- Dung `Purchase Receipt`
- Menu: `Stock > Purchase Receipt` hoac tu `Purchase Order`

### Cac buoc

1. Tao `Purchase Receipt`.
2. Chon kho nhap:
   - `FG Quarantine - VAP`
   - `RM Quarantine - VAP`
3. Nhap item, qty.
4. Gan batch.
5. `Save` -> `Submit`.

## 7.2 Nhap kho noi bo khong qua PO

- Dung `Stock Entry`
- Purpose: `Material Receipt`

### Cac buoc

1. Vao `Stock > Stock Entry`.
2. Bam `New`.
3. Chon `Purpose = Material Receipt`.
4. Nhap kho dich vao dong hang:
   - `t_warehouse`
5. Nhap item, so luong.
6. Neu co batch:
   - chon `Batch No`
   - hoac tao lo moi
7. `Save` -> `Submit`.

### Truong hop dung

- Nhap ton dau ky
- Nhap dieu chinh tang ton
- Nhap hang noi bo khong qua mua hang

## 8. Quy trinh xuat kho

## 8.1 Xuat kho giao khach

- Dung `Delivery Note`
- Xem muc `5.1 Buoc 3` den `Buoc 5`

## 8.2 Xuat kho noi bo

- Dung `Stock Entry`
- Purpose: `Material Issue`

### Cac buoc

1. Vao `Stock > Stock Entry`.
2. Bam `New`.
3. Chon `Purpose = Material Issue`.
4. Nhap:
   - `s_warehouse`
   - `Item Code`
   - `Qty`
5. Neu item co batch:
   - chon `Batch No`
   - hoac dung picker bundle cua ERPNext
6. `Save` -> `Submit`.

### Truong hop dung

- Xuat mau
- Xuat huy
- Xuat su dung noi bo
- Xuat cap phat cho bo phan khac

## 9. Quy trinh chuyen kho giua cac kho

## 9.1 Chuyen kho noi bo thong thuong

- Dung `Stock Entry`
- Purpose: `Material Transfer`

### Cac buoc

1. Vao `Stock > Stock Entry`.
2. Bam `New`.
3. Chon `Purpose = Material Transfer`.
4. Nhap dong hang:
   - `Item Code`
   - `Qty`
   - `s_warehouse`
   - `t_warehouse`
5. Neu item co batch:
   - chon `Batch No`
   - kiem tra dung kho nguon
6. `Save` -> `Submit`.

### Vi du

- `FG Released - VAP` -> `HCM Sellable - VAP`
- `FG Released - VAP` -> `HN Sellable - VAP`
- `RM Quarantine - VAP` -> `RM Released - VAP`

## 9.2 Chuyen tu Quarantine sang Released

### Dieu kien

- Batch da duoc QA release

### Cac buoc

1. Vao `Stock Entry`.
2. Chon `Purpose = Material Transfer`.
3. Chon kho nguon:
   - `FG Quarantine - VAP`
   - hoac `RM Quarantine - VAP`
4. Chon kho dich:
   - `FG Released - VAP`
   - hoac `RM Released - VAP`
5. Chon item, qty, batch.
6. `Save` -> `Submit`.

## 9.3 Chuyen kho tong sang kho chi nhanh

### Cac buoc

1. Tao `Stock Entry` purpose `Material Transfer`.
2. Nguon:
   - `FG Released - VAP`
3. Dich:
   - `HCM Sellable - VAP`
   - hoac `HN Sellable - VAP`
4. Chon batch theo FEFO.
5. `Submit`.

### Kiem soat

- Chuyen dung kho ban hang theo vung
- Neu co theo doi van chuyen, co the tach thanh:
  - `FG Released - VAP` -> `Goods In Transit - VAP`
  - `Goods In Transit - VAP` -> `HCM Sellable - VAP`

## 10. Checklist bat buoc theo tung loai chung tu

## 10.1 Sales Order

- khach hang dung
- gia ban dung
- VAT dung
- kho xuat dung
- so luong dung

## 10.2 Delivery Note

- kho xuat dung
- batch/serial da chon
- lo con han
- lo da release
- so luong du ton

## 10.3 Purchase Receipt

- nha cung cap dung
- kho nhap dung
- so luong thuc nhan dung
- batch dung
- chung tu kem theo day du neu can

## 10.4 Stock Entry

- purpose dung
- kho nguon va kho dich dung
- batch dung
- so luong dung
- ly do dieu chuyen ro rang

## 11. Quy trinh mau de team van hanh

## 11.1 Ban hang nha thuoc

1. Tao `Sales Order` cho `Nha Thuoc An Khang`
2. Chon `PARA-500`, so luong `100`
3. Chon kho `FG Released - VAP`
4. `Submit Sales Order`
5. `Create > Delivery`
6. Tai `Delivery Note`, bam `Pick Serial / Batch No`
7. Chon lo `PARA500-2601-001`
8. `Submit Delivery Note`
9. `Create > Sales Invoice`
10. `Submit Sales Invoice`

## 11.2 Mua hang vao kho Released

1. Tao `Purchase Order` cho `Duoc Lieu Mekong`
2. Them item `PARA-500`
3. `Submit Purchase Order`
4. `Create > Purchase Receipt`
5. Nhap batch
6. `Submit Purchase Receipt`
7. QA release
8. Tao `Stock Entry` chuyen tu `FG Quarantine - VAP` sang `FG Released - VAP`

## 12. Ghi chu van hanh

- Neu can giao hang nhanh, van phai co batch hop le truoc khi submit `Delivery Note`.
- Neu giao dien khong hien ngay thay doi moi, hard refresh `Cmd+Shift+R`.
- Neu chon lo khong ra ket qua, kiem tra lai:
  - item co ton khong
  - kho co ton khong
  - batch da `Released` chua
  - batch co con han khong

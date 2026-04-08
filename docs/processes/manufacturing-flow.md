# Manufacturing Flow

## 1. Muc tieu

- Hoach dinh san xuat theo nhu cau va ton kho.
- Quan ly lo san xuat, BOM, yield, QA va truy vet batch.

## 2. Quy trinh san xuat

1. Tong hop du bao, Sales Order va ton kho.
2. Tao `Production Plan`.
3. Chay MRP tinh nguyen lieu thieu.
4. Tao `Material Request` cho mua hang.
5. Tao `Work Order` theo lo.
6. Xuat nguyen lieu tu kho `RM Released`.
7. Ghi nhan cong doan va hao hut.
8. Tao `Stock Entry` manufacture.
9. Sinh batch thanh pham.
10. Nhap `FG Quarantine`.
11. QA thuc hien release.
12. Chuyen sang `FG Released`.

## 3. Subcontracting

1. Tao PO subcontracting.
2. Gui nguyen lieu toi nha gia cong.
3. Nhan thanh pham ve.
4. QC va batch release.
5. Hach toan chi phi gia cong.

## 4. Business rules

- BOM phai duoc version control.
- Yield vuot tolerance phai xin phe duyet deviation.
- Batch thanh pham phai link duoc toi batch nguyen lieu chinh.
- Thanh pham san xuat xong khong duoc xuat thang khi chua QA release.

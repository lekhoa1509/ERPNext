# Inventory and Warehouse Flow

## 1. Cau truc kho de xuat

- `WH-BD-RM-QUA`: nguyen lieu quarantine
- `WH-BD-RM-REL`: nguyen lieu released
- `WH-BD-FG-QUA`: thanh pham quarantine
- `WH-BD-FG-REL`: thanh pham released
- `WH-HCM-FG-REL`: kho ban HCM
- `WH-HN-FG-REL`: kho ban HN
- `WH-RETURNS`: hang tra ve
- `WH-REJECTED`: hang khong dat
- `WH-EXPIRED`: hang het han
- `WH-COLD-2-8`: kho lanh 2-8C

## 2. Inbound flow

1. Nhan hang tai kho.
2. Kiem tra chung tu va so luong.
3. Tao `Purchase Receipt`.
4. Nhap vao kho `Quarantine`.
5. Tao `Quality Inspection`.
6. QA release.
7. Chuyen kho noi bo sang `Released`.

## 3. Outbound flow

1. Nhan nhu cau giao tu `Sales Order`.
2. Tao `Pick List`.
3. Chon batch theo FEFO.
4. Scan batch/serial/barcode khi lay hang.
5. Dong goi va tao `Delivery Note`.
6. Cap nhat `Stock Ledger`.

## 4. Internal transfer flow

1. Tao `Stock Entry` loai Material Transfer.
2. Xuat kho nguon.
3. Van chuyen noi bo.
4. Nhan kho dich.
5. Neu la kho lanh, ghi nhan nhiet do trong qua trinh van chuyen.

## 5. Return flow

1. Khach tra hang.
2. Tao `Sales Return`.
3. Dua hang vao `WH-RETURNS`.
4. QA danh gia:
   - con nguyen ven
   - con han
   - dieu kien bao quan
5. Quy dinh tiep theo:
   - tra lai kho su dung
   - huy hang
   - gui nha cung cap

## 6. Recall flow

1. QA/Regulatory khoi tao `PH Recall Case`.
2. Khoa batch lien quan.
3. Truy vet:
   - Purchase Receipt
   - Work Order
   - Delivery Note
   - Sales Invoice
4. Xac dinh ton dang con trong kho va da phan bo den khach nao.
5. Tao lenh thu hoi va giam sat xu ly.

## 7. Business rules

- FEFO la rule mac dinh cho hang co han dung.
- Kho `Quarantine` va `Rejected` khong duoc xuat ban.
- Batch co `temperature_excursion_flag = 1` phai hold.
- Chu ky kiem ke ABC:
  - A: hang tuan
  - B: hang thang
  - C: hang quy

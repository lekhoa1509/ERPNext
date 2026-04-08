# Security and Permission Design

## 1. Role model

- `System Manager`
- `ERP Admin`
- `Sales User`
- `Sales Manager`
- `Warehouse User`
- `Warehouse Manager`
- `Procurement User`
- `Procurement Manager`
- `QA User`
- `QA Manager`
- `Production Planner`
- `Production Manager`
- `Accountant`
- `Finance Manager`
- `Auditor`

## 2. Permission rule theo nghiep vu

### Sales

- Sales User:
  - tao va xem lead/opportunity/quotation/sales order thuoc territory cua minh
  - khong duoc xem buying rate
- Sales Manager:
  - duyet quotation
  - xem dashboard theo team/vung

### Warehouse

- Warehouse User:
  - thao tac Receipt, Delivery, Transfer tai cac kho duoc gan
  - khong duoc sua gia
- Warehouse Manager:
  - duyet stock adjustment
  - xem ton toan bo kho minh phu trach

### QA

- QA User:
  - tao va nhap ket qua `Quality Inspection`
- QA Manager:
  - release/hold batch
  - khoi tao recall

### Finance

- Accountant:
  - AP/AR, Payment Entry, Journal Entry
- Finance Manager:
  - duyet vuot credit limit
  - khoa ky
  - duyet dieu chinh tai chinh

## 3. Data access control

- Dung `User Permission` theo:
  - Company
  - Branch
  - Warehouse
  - Territory
  - Cost Center
- Dung `permission_query_conditions` cho quy tac dac thu.
- Bat 2FA cho Admin, QA Manager, Finance Manager.
- Integration user rieng cho API.
- Bat versioning va audit trail.

## 4. Chinh sach van hanh

- Khong cho phep sua chung tu sau khi submit neu khong amend.
- Cancel/amend phai co role manager.
- File dinh kem nhay cam can luu tren object storage private.

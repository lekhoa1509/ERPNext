# Solution Design ERPNext cho doanh nghiep duoc tai Viet Nam

## 1. Ho so doanh nghiep mau

- Ten doanh nghiep: Viet An Pharma JSC
- Linh vuc: San xuat va phan phoi duoc pham OTC/ETC, TPBVSK
- Quy mo: 420 nhan su
- Quoc gia: Viet Nam
- Mo hinh van hanh: Hybrid B2B/B2C
- Co so van hanh:
  - 1 nha may GMP-WHO tai Binh Duong
  - 2 kho phan phoi tai HCM va Ha Noi
  - kenh B2B cho nha thuoc, benh vien, dai ly
  - kenh B2C qua website/mobile app

## 2. Muc tieu he thong

- Quan ly end-to-end tu Lead den thu tien.
- Quan ly batch, han dung, quarantine, QA release va FEFO.
- Quan ly MRP va san xuat theo lo.
- Quan ly cong no, VAT, hoa don dien tu phu hop thuc te Viet Nam.
- Tich hop website, payment gateway, WMS/handheld, CRM/DMS, IoT nhiet do.

## 3. Nguyen tac thiet ke

- Uu tien core ERPNext truoc, custom sau khi fit-gap.
- Toan bo custom dac thu duoc gom vao app `pharma_vn`.
- Du lieu Item, Batch, Warehouse, Customer, Supplier phai duoc chuan hoa truoc go-live.
- Thiet ke permission theo company, branch, warehouse, territory va cost center.
- Moi flow xuat ban phai di qua gate kiem tra batch release va shelf-life.

## 4. Module su dung

| Module | Vai tro | Muc do |
| --- | --- | --- |
| CRM | Lead, Opportunity, customer onboarding | Core |
| Selling | Quotation, Sales Order, Delivery, Sales Invoice | Core + custom rules |
| Buying | RFQ, Supplier Quotation, PO, GRN, AP | Core + custom rules |
| Stock | Multi-warehouse, batch, expiry, FEFO | Core + custom rules |
| Manufacturing | BOM, Work Order, Production Plan, MRP | Core + custom rules |
| Quality | Incoming QC, in-process QC, batch release | Core + custom supplement |
| Accounts | AR/AP/GL/VAT/bank reconciliation | Core + local integration |
| Asset/Maintenance | May moc, bao tri thiet bi | Core |
| `pharma_vn` | Batch release, recall, temp log, API integration | Custom |

## 5. Data model tong the

### Master data

- `Item`
- `Item Group`
- `Batch`
- `Warehouse`
- `Customer`
- `Supplier`
- `Price List`
- `Tax Template`
- `BOM`

### Transaction data

- `Quotation`
- `Sales Order`
- `Delivery Note`
- `Sales Invoice`
- `Payment Entry`
- `Material Request`
- `Purchase Order`
- `Purchase Receipt`
- `Purchase Invoice`
- `Production Plan`
- `Work Order`
- `Stock Entry`
- `Quality Inspection`

### Custom DocType

- `PH Batch Release`
- `PH Temperature Log`
- `PH Recall Case`

## 6. Governance va workflow

- Bao gia giam gia vuot nguong phai duyet.
- Don hang vuot credit limit phai duyet boi Finance.
- PO theo cap gia tri va loai mua hang.
- Batch chi duoc ban neu da co `PH Batch Release` = Released.
- Dieu chinh ton kho am phai qua duyet Warehouse Manager + Finance.

## 7. Tich hop chinh

- Website/mobile app:
  - dong bo catalog, gia, ton kha dung
  - day order vao ERPNext
  - nhan trang thai thanh toan, giao hang, hoa don
- Payment gateway:
  - VNPay, MoMo, virtual account
- E-invoice:
  - Viettel, VNPT, MISA meInvoice
- WMS/handheld:
  - pick-pack-ship, scan batch/barcode
- CRM/DMS:
  - lead/opportunity/order capture
- IoT:
  - nhiet do kho lanh, canh bao cold-chain

## 8. Ky thuat va deployment

- ERPNext App nodes
- MariaDB primary + read replica
- Redis cache/queue/socketio
- Scheduler + workers short/default/long
- Object storage cho attachments
- Docker deployment cho UAT/PROD
- Monitoring: Grafana, Loki, Sentry

## 9. Pham vi giai doan

### Phase 1

- Master data
- CRM
- Selling
- Buying
- Stock
- Accounts

### Phase 2

- Quality
- Batch release
- E-invoice
- Payment gateway
- Dashboards

### Phase 3

- Manufacturing
- MRP
- Recall
- Temp monitoring
- WMS/handheld integration

### Phase 4

- B2C website/mobile
- DMS/SFA
- Advanced analytics

## 10. KPI sau go-live

- OTIF giao hang
- Fill rate theo kho
- Aging cong no
- Near-expiry inventory
- Gross margin theo kenh
- QC release turnaround time
- Yield variance
- Inventory accuracy

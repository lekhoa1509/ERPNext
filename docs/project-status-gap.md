# Project Status Gap

Bang tong hop nhanh tinh trang hien tai cua repo `ERPNext / pharma_vn`, gom 3 nhom:

- `Da co`: nhung gi da thay ro trong code/tai lieu
- `Con thieu`: nhung gi chua day du de van hanh thuc te
- `Uu tien`: muc do nen lam tiep

| Hang muc | Da co | Con thieu | Uu tien |
| --- | --- | --- | --- |
| Desktop Home / Sidebar | Co dashboard home custom, sidebar module custom, shell UI rieng, co co che refresh va chinh desktop layout co ban | Dong bo layout giua Desktop Edit, sidebar custom, workspace rail chua that su muot trong moi tinh huong; can tiep tuc on dinh hoa | Cao |
| AI Assistant UI | Da co widget AI rieng, co giao dien moi, co send message, refresh, minimize, drag widget | Chua co upload file, attachment thuc, emoji picker thuc, lich su hoi dap ben vung, xu ly mobile/toi uu UX sau cung | Trung binh |
| AI Assistant nghiep vu ERP | Da co intent tao customer, draft Sales Order, report, stock lookup, help/SOP, va bo tri thuc quy trinh ERP Viet Nam | Chua thanh copilot ERP day du: chua co xu ly da buoc, xac nhan thao tac nhay cam, context theo man hinh dang mo, audit log day du | Cao |
| Ban hang | Da co tai lieu quy trinh, custom JS cho Sales Order / Delivery Note / Sales Invoice, co API document flow va mot so validation | Chua thay mot bo quy trinh sales end-to-end duoc test day du voi workflow approval, credit control, return, e-invoice thuc chien | Cao |
| Mua hang | Da co SOP mua hang, custom JS Purchase Receipt, automation cho inbound va luong kho layout | Chua thay bo quy trinh AP/3-way match/landed cost/QA release duoc dong goi thanh luong hoan chinh co test | Cao |
| Kho / ton kho | Da co stock API, warehouse layout 2D, WH Cell / WH Cell Stock / layout service, co stock lookup trong AI | Chua day du bao cao van hanh kho thuc dung nhu stock aging, near-expiry, fill rate, inventory accuracy, cycle count UI | Cao |
| Warehouse Layout 2D | Da co DocType, API, preview, service, custom field lien quan `wh_layout`, `wh_cell` | Chua thay day du thao tac quan tri hang loat, bulk move, bao cao movement, va test tu dong | Trung binh |
| Batch / QA Release | Da co y tuong, tai lieu va mot so rule nghiep vu lien quan batch, quarantine, released | Chua thay trien khai day du cac Custom DocType trong docs nhu `PH Batch Release` de van hanh release/hold/reject hoan chinh | Cao |
| Recall / truy vet | Da co tai lieu nghiep vu recall, traceability trong docs va huong nghiep vu trong AI | Chua thay Custom DocType / flow xu ly recall end-to-end thuc te trong app | Cao |
| Temperature / cold-chain | Da co scope va nhac den IoT / temperature excursion trong docs va README | Chua thay `PH Temperature Log`, canh bao cold-chain, dashboard va xu ly ngoai le duoc trien khai tron ven | Cao |
| Ke toan / VAT | Da co docs accounting flow, tax seed logic Viet Nam, tax templates bootstrap 0/5/8/10 | Chua thanh compliance engine; chua co bo xu ly nghiep vu VAT/e-invoice day du theo tinh huong thuc te va canh bao phap ly tu dong | Cao |
| E-invoice | Da co dinh huong tich hop trong docs va custom field lien quan trang thai hoa don dien tu | Chua thay integration provider thuc te voi Viettel/VNPT/MISA meInvoice | Cao |
| Payment gateway | Da co docs / scope va API payments | Chua thay ket noi thuc te voi VNPay, MoMo, virtual account theo luong production | Trung binh |
| Website / mobile / order integration | Da co docs tich hop va mot so API orders, stock, payments | Chua thay adapter production-ready cho website/mobile/B2C hoac webhook flow hoan chinh | Trung binh |
| Dashboard / KPI | Da co API dashboard va giao dien dashboard home | Chua day du KPI quan tri thuc chien nhu near-expiry, OTIF, QC turnaround, gross margin theo kenh, aging ton kho | Trung binh |
| Bao mat / phan quyen | Da co docs security-permission va mot so guard permission trong backend | Chua thay bo permission matrix duoc kiem thu day du theo role/user/company/warehouse | Cao |
| Demo data / bootstrap | Da co bootstrap demo, defaults, custom fields, workflows, scripts chay local | Chua co bo migration/seed du lieu mau co test de dung on dinh qua nhieu lan khoi tao | Trung binh |
| Test / QA ky thuat | Gan nhu chua co test tu dong; thu muc `tests` hien dang rong | Can bo test cho API, automation, AI assistant, warehouse layout, quy trinh sales/purchase/stock | Cao |
| Deployment production readiness | Da co Docker compose, scripts start/stop/logs, docs deployment | Chua thay bo CI/CD, backup/restore rehearsal, monitoring, rollback runbook, hardening production day du | Trung binh |

## Tong ket nhanh

### Uu tien cao nen lam tiep ngay

1. On dinh hoa desktop/sidebar/layout de UI phan he phan anh dung thay doi cua user.
2. Hoan thien `PH Batch Release`, recall, temperature log va cac flow dược cot loi.
3. Bo sung test tu dong cho sales, purchase, stock, warehouse layout, AI assistant.
4. Hoan thien e-invoice, VAT va guardrail compliance muc nghiep vu.
5. Nang AI Assistant tu muc tra loi + thao tac don gian len copilot ERP co quy trinh.

### Uu tien trung binh

1. Dashboard KPI van hanh thuc chien.
2. Payment gateway, website/mobile integration.
3. Warehouse layout thao tac nang cao, bulk action, movement report.
4. Deployment/monitoring/runbook cho production.

### Uu tien thap hon

1. Tinh nang giao dien phu tro nhu emoji/attachment thuc trong AI.
2. Tinh chinh them visual desktop shell neu khong anh huong nghiep vu.

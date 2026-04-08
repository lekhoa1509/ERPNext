# ERPNext Pharma Vietnam - Tài Liệu Tổng Hợp Hiện Trạng

## 1. Mục tiêu phần mềm

Phần mềm hiện tại là một custom app Frappe/ERPNext tên `pharma_vn`, phục vụ bài toán vận hành doanh nghiệp dược tại Việt Nam. Hướng triển khai là:

- giữ ERPNext core làm nền;
- gom toàn bộ custom vào app riêng;
- ưu tiên các flow dược cốt lõi như batch release, quarantine/released, recall, cold-chain, VAT, e-invoice, warehouse layout, AI assistant;
- làm theo hướng có thể test được và mở rộng dần thành hệ thống production-ready.

## 2. Cấu trúc repo hiện tại

- `apps/pharma_vn/`: custom app chính.
- `apps/pharma_vn/pharma_vn/api/`: API phục vụ UI, integration và nghiệp vụ.
- `apps/pharma_vn/pharma_vn/automation/`: hook nghiệp vụ khi document validate/submit/cancel.
- `apps/pharma_vn/pharma_vn/services/`: service thuần Python cho business rule, dễ test và tái sử dụng.
- `apps/pharma_vn/pharma_vn/warehouse_layout_2d/`: module quản lý layout kho 2D.
- `apps/pharma_vn/pharma_vn/ai_assistant/`: AI assistant và copilot logic.
- `apps/pharma_vn/pharma_vn/pharma_operations/doctype/`: DocType custom cho các flow dược.
- `apps/pharma_vn/pharma_vn/public/js/` và `public/css/`: giao diện desktop shell, ERP home, AI widget, custom client script.
- `apps/pharma_vn/pharma_vn/setup/`: custom fields, defaults, workflow bootstrap.
- `apps/pharma_vn/pharma_vn/tests/`: test tự động mức unit/service/helper.
- `docs/`: tài liệu thiết kế, quy trình, kiến trúc, deployment.

## 3. Những gì phần mềm đang có

### 3.1. UI desktop và workspace

Hiện đã có hai lớp UI chính:

- `erp_home.js` + `erp_home.css`: custom desktop home theo kiểu dashboard + module navigation.
- `pharma_byd.js` + `pharma_byd.css`: shell/sidebar/layout theo hướng giống command deck.

Hiện đã có:

- cache layout desktop theo user;
- đồng bộ tương đối giữa server layout và local storage;
- ép các icon bắt buộc như `Warehouse Layout 2D` luôn tồn tại;
- loại bỏ icon không muốn hiển thị như `AI Assistant` khỏi desktop icon grid truyền thống;
- sidebar module rail và desktop shell tùy biến.

Phần đã được ổn định thêm:

- khi fetch layout từ server sẽ cập nhật lại local cache;
- tránh trường hợp layout local cũ ghi đè lên layout mới của user;
- tách rõ logic “đã fetch server layout hay chưa”.

### 3.2. Warehouse Layout 2D

Module này hiện đã có:

- DocType `WH Layout`
- DocType `WH Cell`
- DocType `WH Cell Stock`
- DocType `WH Cell Movement`
- service dựng grid, auto-generate cell, validate cell assignment, movement stock theo cell
- form preview 2D cho layout
- workspace riêng cho warehouse layout

Ý nghĩa nghiệp vụ:

- cho phép quản lý vị trí tồn kho trong kho vật lý thay vì chỉ ở mức warehouse;
- hỗ trợ nhập kho có gắn `wh_layout` và `wh_cell`;
- mở nền tảng cho các use case như putaway, picking, movement trace.

### 3.3. Flow Purchase Receipt và inbound kho

Hiện đã có:

- validate bắt buộc chọn `WH Cell` nếu warehouse dùng layout 2D;
- tự động tạo `PH Batch Release` draft khi item cần QA;
- sync tồn kho vào `WH Cell Stock`;
- ghi movement history vào `WH Cell Movement`;
- hỗ trợ reverse movement khi hủy chứng từ.

### 3.4. Flow Batch Release / QA

Hiện đã có:

- API `pharma_vn.api.quality.release_batch`
- service `pharma_vn.services.quality`
- DocType `PH Batch Release`
- custom field trên `Batch` như `batch_status`, `release_date`, `released_by`, `temperature_excursion_flag`

Rule chính:

- batch đi theo state machine `Draft -> QA -> Released/Hold/Rejected`;
- decision chỉ nhận `Released`, `Hold`, `Rejected`;
- khi `Released` thì update Batch để mở điều kiện bán;
- khi `Hold` hoặc `Rejected` thì batch không còn sellable trong flow giao hàng.

### 3.5. Recall / truy vết

Hiện đã có:

- API `pharma_vn.api.integrations.trigger_recall`
- service tạo dữ liệu recall
- DocType `PH Recall Case`

Rule chính:

- recall đi theo state machine `Open -> Investigating -> Executing -> Closed`;
- khi mở recall case sẽ đếm trước số `Delivery Note` bị ảnh hưởng;
- sau khi recall sẽ cập nhật `Batch Status = Recalled`.

### 3.6. Temperature log / cold-chain

Hiện đã có:

- API `pharma_vn.api.integrations.log_temperature`
- service đánh giá temperature excursion
- DocType `PH Temperature Log`
- scheduler nền cho các check theo giờ/ngày

Rule chính:

- hệ thống so sánh `temperature_c` với `min_temp` và `max_temp`;
- nếu vượt ngưỡng và có `batch_no`, batch sẽ bị đưa về `Hold`;
- có cờ `temperature_excursion_flag` để chặn bán.

### 3.7. Log system và alert

Hiện đã có:

- file log vận hành tại `apps/pharma_vn/logs/pharma_operations.log`
- DocType `PH Alert Log`
- scheduler alert cho:
  - temperature excursion
  - invoice fail
  - stock mismatch giữa `WH Cell Stock` và `Bin`
- push `Notification Log` tới role phụ trách

Mục tiêu:

- vừa có log file đơn giản để vận hành local/server;
- vừa có bản ghi alert có thể assign và theo dõi trong ERP.

### 3.8. Sales / Delivery / Invoice

Hiện đã có:

- custom fields cho `Sales Order` để map nghiệp vụ kiểu SAP ByD;
- validate Sales Order, sync overview/contact/status/audit fields;
- check credit status;
- document flow API cho `Sales Order -> Delivery Note -> Sales Invoice -> Payment Entry`;
- validate batch sellable ở `Delivery Note`.

### 3.9. VAT / e-invoice / compliance guardrail

Hiện đã có lớp compliance mới:

- service `pharma_vn.services.compliance`
- API `review_sales_invoice`
- API `build_sales_e_invoice`
- hook validate `Sales Invoice`
- hook generate `e_invoice_payload_json`

Rule hiện tại:

- chỉ chấp nhận VAT rate trong tập `0, 5, 8, 10`;
- tính tổng net / VAT / gross theo từng dòng;
- chặn invoice nếu thiếu company, customer, posting date, item;
- chặn e-invoice nếu thiếu tax identity quan trọng;
- cảnh báo nếu invoice date bất thường, posting future date, hoặc `Issued` nhưng chưa có `e_invoice_no`.

Lưu ý:

- phần này mới ở mức compliance engine nội bộ;
- chưa tích hợp thật với provider Viettel/VNPT/MISA;
- payload hiện được giữ ở dạng neutral để map provider sau này.

### 3.10. Traceability full

Hiện đã có:

- API `pharma_vn.api.operations_control.get_batch_traceability`
- forward trace:
  - batch -> `Delivery Note` -> customer
  - batch -> `Sales Invoice`
- backward trace:
  - batch -> `Purchase Receipt` -> supplier
- summary gộp customer/supplier/count để làm one-click report

Giới hạn hiện tại:

- mới trace từ các chứng từ chuẩn phổ biến;
- chưa gom hết `Stock Entry`, return flow và trace theo serial bundle phức tạp.

### 3.11. CAPA / Deviation

Hiện đã có:

- DocType `PH Deviation`
- DocType `PH CAPA`
- API tạo Deviation / CAPA
- field `assigned_to`, status, root cause, immediate action, effectiveness review
- `track_changes = 1` để có audit trail mức DocType

Ý nghĩa:

- phát hiện lỗi
- có quy trình xử lý
- có người chịu trách nhiệm
- có lịch sử thay đổi và comment/audit

### 3.12. AI Assistant

Hiện đã có:

- widget AI trên desk;
- bootstrap status và sample prompt;
- gọi OpenAI Responses API;
- intent xử lý:
  - `create_customer`
  - `create_sales_order_draft`
  - `create_auto_email_report`
  - `stock_lookup`
  - `help`
  - `erp_workflow_copilot`

Điểm mạnh hiện tại:

- có runtime context để giảm hallucination;
- có local help routing cho SOP và nghiệp vụ phổ biến;
- có local copilot routing cho các workflow:
  - batch release
  - recall
  - temperature excursion
  - e-invoice/VAT review

Giới hạn hiện tại:

- copilot mới ở mức hướng dẫn quy trình và thu thập context;
- chưa tự động thực thi các thao tác nhạy cảm theo chuỗi nhiều bước;
- chưa có audit trail đầy đủ cho mọi hành động AI.

## 4. Những custom DocType đang có

### Có sẵn từ trước

- `WH Layout`
- `WH Cell`
- `WH Cell Stock`
- `WH Cell Movement`

### Đã bổ sung cho nghiệp vụ dược

- `PH Alert Log`
- `PH Batch Release`
- `PH Temperature Log`
- `PH Recall Case`
- `PH Deviation`
- `PH CAPA`

## 5. Những API chính đang có

- `pharma_vn.api.quality.release_batch`
- `pharma_vn.api.quality.send_batch_to_qa`
- `pharma_vn.api.integrations.log_temperature`
- `pharma_vn.api.integrations.trigger_recall`
- `pharma_vn.api.operations_control.transition_batch_state`
- `pharma_vn.api.operations_control.transition_recall_state`
- `pharma_vn.api.operations_control.get_batch_traceability`
- `pharma_vn.api.operations_control.create_deviation`
- `pharma_vn.api.operations_control.create_capa`
- `pharma_vn.api.compliance.review_sales_invoice`
- `pharma_vn.api.compliance.build_sales_e_invoice`
- `pharma_vn.api.stock.get_sellable_stock`
- `pharma_vn.api.orders.create_b2b_order`
- `pharma_vn.api.document_flow.get_document_flow`
- `pharma_vn.api.ai_assistant.chat`
- `pharma_vn.api.warehouse_layout.get_layout`

## 6. Hook và automation đang có

Trong `hooks.py`, hiện đang bật:

- `Sales Order.validate`
- `Delivery Note.validate`
- `Sales Invoice.validate`
- `Sales Invoice.on_submit`
- `Purchase Receipt.validate`
- `Purchase Receipt.on_submit`
- `Purchase Receipt.on_cancel`
- scheduler hourly và daily
- operational alert scheduler cho temperature, invoice fail, stock mismatch

Ý nghĩa:

- ưu tiên chặn lỗi ở thời điểm validate;
- sinh dữ liệu phụ trợ ở thời điểm submit;
- để scheduler xử lý tác vụ nền như temperature excursion và near-expiry.

## 7. Bộ test hiện tại

Đã có test tự động mức unit/helper/service cho:

- alert
- state machine
- traceability
- compliance
- AI copilot
- sales helper
- purchase helper
- stock rule
- warehouse layout service

Lệnh đang chạy được:

```bash
python3 -m unittest discover -s apps/pharma_vn/pharma_vn/tests -p 'test_*.py'
python3 -m compileall apps/pharma_vn/pharma_vn
```

Trạng thái khi viết tài liệu này:

- `19` tests pass
- compile pass

Lưu ý:

- test hiện tại không phụ thuộc bench/Frappe thật;
- đang dùng stub để kiểm tra business logic cốt lõi nhanh;
- chưa thay thế cho integration/UAT trên site ERPNext thật.

## 8. Các file quan trọng nên đọc đầu tiên

- `apps/pharma_vn/pharma_vn/hooks.py`
- `apps/pharma_vn/pharma_vn/services/quality.py`
- `apps/pharma_vn/pharma_vn/services/compliance.py`
- `apps/pharma_vn/pharma_vn/automation/purchase_receipt.py`
- `apps/pharma_vn/pharma_vn/automation/sales_order.py`
- `apps/pharma_vn/pharma_vn/automation/sales_invoice.py`
- `apps/pharma_vn/pharma_vn/api/document_flow.py`
- `apps/pharma_vn/pharma_vn/ai_assistant/service.py`
- `apps/pharma_vn/pharma_vn/warehouse_layout_2d/service.py`
- `apps/pharma_vn/pharma_vn/setup/custom_fields.py`

## 9. Những gì còn thiếu hoặc mới ở mức skeleton

### E-invoice production

Chưa có:

- adapter provider thật cho Viettel/VNPT/MISA
- callback/webhook nhận trạng thái phát hành
- retry queue và reconciliation
- quản lý mẫu số, ký hiệu, serial thật

### VAT/compliance nâng cao

Chưa có:

- rule chi tiết theo từng case nghiệp vụ
- rule riêng cho return, adjustment, replacement, promotion, hàng mẫu
- mapping tax code đầu vào/đầu ra chuẩn báo cáo thuế
- báo cáo đối soát VAT theo kỳ

### AI copilot nâng cao

Chưa có:

- confirm action cho thao tác nhạy cảm
- multi-step execution thực sự
- context theo màn hình user đang mở
- audit log đầy đủ
- memory/history bền vững

### Warehouse layout nâng cao

Chưa có:

- bulk move
- movement report nâng cao
- cycle count UI
- putaway strategy / picking strategy

### Traceability / quality

Đã có nền tảng:

- recall state machine
- traceability forward/backward mức chứng từ chuẩn
- Deviation / CAPA DocType

Chưa có:

- dashboard QC turnaround
- traceability đủ cả Stock Entry/return/bundle phức tạp
- link tự động từ alert sang deviation/capa

## 10. Hướng phát triển tương lai

### Giai đoạn 1. Ổn định production nền tảng

- chạy migration để materialize toàn bộ DocType và custom field mới
- UAT end-to-end các flow Sales, Purchase, Stock, Recall, Temperature, Batch Release
- thêm integration test trên site ERPNext thật
- chuẩn hóa seed data demo và bootstrap repeatable

### Giai đoạn 2. Compliance thật sự

- xây adapter e-invoice cho từng provider
- đưa `e_invoice_payload_json` thành hàng chờ phát hành
- lưu request/response theo từng lần phát hành
- bổ sung dashboard lỗi phát hành hóa đơn điện tử
- xây rule VAT theo loại nghiệp vụ

### Giai đoạn 3. Copilot ERP

- chuyển từ “gợi ý thao tác” sang “đề xuất kế hoạch + xin xác nhận + thực thi”
- thêm action confirmation cho tạo/chỉnh/sumbit chứng từ
- hỗ trợ workflow có checkpoint như:
  - release batch
  - recall case
  - stock transfer quarantine -> released
  - invoice compliance review
- lưu audit log AI action

### Giai đoạn 4. Kho và truy vết nâng cao

- cycle count theo cell
- near-expiry dashboard
- recall trace report
- hàng đợi xử lý cold-chain excursion
- hỗ trợ handheld/WMS integration

### Giai đoạn 5. Production readiness đầy đủ

- CI/CD
- rollback plan
- monitoring
- alerting
- backup rehearsal
- permission matrix theo role/company/warehouse

## 11. Nguyên tắc kỹ thuật đang áp dụng

- business rule quan trọng nên đi vào `services/` để dễ test;
- API chỉ nên parse input, gọi service, trả response;
- hook automation chỉ nên nối document lifecycle với service;
- UI desktop không được phép tự coi local storage là nguồn chân lý nếu server đã có layout mới;
- AI chỉ nên tự động hóa phần có guardrail rõ, phần nhạy cảm cần confirm.

## 12. Kết luận

Hệ thống hiện đã vượt mức skeleton ở một số mảng quan trọng:

- có desktop shell và workspace riêng;
- có warehouse layout 2D chạy được;
- có flow batch release / temperature / recall ở mức nền tảng;
- có compliance engine bước đầu cho VAT và e-invoice;
- có AI Assistant và workflow copilot mức đầu;
- có bộ test tự động để giữ nhịp phát triển an toàn hơn.

Nhưng để đi production thực chiến, các ưu tiên tiếp theo vẫn là:

- integration thật cho e-invoice;
- end-to-end UAT trên site ERPNext;
- multi-step AI copilot có xác nhận;
- hardening permission, monitoring, và traceability.

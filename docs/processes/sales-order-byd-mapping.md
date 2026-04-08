# Sales Order SAP ByD Mapping

## Muc tieu

Tai lieu nay map form `Sales Order` cua ERPNext theo bo cuc va quy trinh van hanh gan voi SAP Business ByDesign, nhung da dieu chinh cho doanh nghiep duoc tai Viet Nam.

## Nguyen tac thiet ke

- Giữ `Sales Order` core của ERPNext làm chứng từ chính.
- Dùng custom field để bổ sung header nghiệp vụ thay vì sửa core form.
- Các thông tin tóm tắt như `Account`, `Ship-To`, `Bill-To`, `Credit Status`, `Delivery Status`, `Invoice Status` được tự đồng bộ từ dữ liệu chuẩn của ERPNext.
- Workflow approval đi theo logic dược B2B: `In Preparation -> Pending Credit Review -> Pending Sales Approval -> Pending Finance Approval -> Approved`.

## Mapping form header

### 1. Account / Contact / Ship-To / Bill-To

- `Account Name`: map từ `customer_name`
- `Account Address`: map từ `address_display`
- `Contact`, `Phone`, `E-Mail`: map từ `contact_person`, `contact_phone`, `contact_mobile`, `contact_email`
- `Ship-To Name`, `Ship-To Address`: map từ `shipping_address_name`, `shipping_address`
- `Bill-To Name`, `Bill-To Address`: map từ `customer` và `address_display`

### 2. General

- `Description`: `pharma_order_description`
- `External Reference`: `pharma_external_reference`, sync 2 chiều với `po_no`
- `Requested Date`: `pharma_requested_date`, mặc định lấy từ `delivery_date`
- `Issue Date`: `pharma_issue_date`, mặc định lấy từ `transaction_date`
- `Price In`: `pharma_price_basis`
- `Origin`: `pharma_origin`
- `Credit Status`: `pharma_credit_status`
- `Allocation Status`: `pharma_allocation_status`
- `Send Order Confirmation`: `pharma_send_order_confirmation`

### 3. Organizational Assignment

- `Employee Responsible`: `pharma_employee_responsible`
- `Sales Unit`: `pharma_sales_unit`
- `Sales Organization`: `pharma_sales_organization`
- `Distribution Channel`: `pharma_distribution_channel`
- `Revenue Contract ID/Description`: `pharma_revenue_contract_id`, `pharma_revenue_contract_description`

### 4. Delivery / Payment / Invoicing

- `Delivery Status`: `pharma_delivery_status`
- `Delivery Priority`: `pharma_delivery_priority`
- `Complete Delivery`: `pharma_complete_delivery`
- `Delivery Block`: `pharma_delivery_block`
- `Shipping Condition`: `pharma_shipping_condition`
- `Incoterms Location`: `pharma_incoterms_location`
- `Total Discount ID / % / Amount`: bộ field `pharma_total_discount_*`
- `Payment Method`: `pharma_payment_method`
- `Payment Reference Type`: `pharma_payment_reference_type`
- `Invoice Status`: `pharma_invoice_status`
- `Invoice Block`: `pharma_invoice_block`
- `Approval Status`: `pharma_approval_status`
- `Approval Note`: `pharma_approval_note`

### 5. Approval Process / Output History

- `Last Approved By`, `Last Approved On`
- `Reason for Rejection`
- `Last Confirmation Sent On`, `Last Confirmation Sent To`

## Workflow nghiep vu de xuat

1. Sales tạo SO ở trạng thái `In Preparation`.
2. Bấm `Submit for Review` khi đã chốt hàng, giá, ngày giao, địa chỉ và PO khách hàng.
3. Kế toán kiểm tra công nợ và hạn mức tín dụng ở `Pending Credit Review`.
4. Nếu đạt, chuyển sang `Pending Sales Approval`.
5. Sales Manager rà lại chiết khấu, điều khoản giao hàng, kênh bán và duyệt sang `Pending Finance Approval`.
6. Finance phê duyệt cuối cùng, chứng từ sang `Approved`.
7. Sau khi approved, kho mới được pick theo batch đã `Released` và nguyên tắc FEFO.
8. Nếu có lý do từ chối, bắt buộc nhập `Reason for Rejection` trước khi đưa về `Rejected`.

## Quy tac van hanh cho doanh nghiep duoc

- Chỉ dùng `Sales Order` cho hàng thương mại đã có sản phẩm hợp lệ và còn hạn dùng theo quy định khách hàng.
- Không cho phát hành giao hàng nếu batch chưa QA release.
- Với khách bệnh viện, nên dùng `Distribution Channel = Hospital` và `Payment Reference Type = Contract`.
- Với nhà thuốc/đại lý, có thể dùng `Distribution Channel = Pharmacy/Distributor` và `Payment Reference Type = Customer PO`.
- `Credit Status` phải phản ánh đồng thời trạng thái thẩm định khách hàng và kiểm tra hạn mức tín dụng.

## Du lieu mau trong site

Bootstrap hiện tạo:

- `Benh Vien Binh Dan`
- `Nha Thuoc An Khang`
- contact, bill-to, ship-to cho từng khách hàng
- một `Sales Order` mẫu B2B dược để UAT luồng phê duyệt

## File lien quan

- `apps/pharma_vn/pharma_vn/setup/custom_fields.py`
- `apps/pharma_vn/pharma_vn/automation/sales_order.py`
- `apps/pharma_vn/pharma_vn/setup/workflows.py`
- `apps/pharma_vn/pharma_vn/public/js/sales_order.js`

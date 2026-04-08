# Sales Flow

## 1. Muc tieu

- Quan ly tu dau moi kinh doanh den thu tien.
- Dam bao don ban chi duoc xuat khi du ton, batch da release va con han su dung theo chinh sach.

## 2. B2B sales flow

1. Tao `Lead` tu sales rep, telesales, CRM, website.
2. Xac minh lead:
   - loai khach hang
   - khu vuc ban
   - giay phep kinh doanh duoc
   - kha nang tin dung
3. Chuyen `Lead` thanh `Opportunity`.
4. Tao `Customer` khi du ho so:
   - `customer_channel`
   - `license_no`
   - `license_expiry`
   - `sales_region`
   - `credit_limit`
5. Tao `Quotation` theo:
   - bang gia
   - hop dong
   - chuong trinh khuyen mai
   - VAT
6. He thong kiem tra:
   - discount threshold
   - margin toi thieu
   - gia theo customer group
7. Neu vuot nguong, `Quotation` vao workflow approval.
8. Khi khach hang dong y, tao `Sales Order`.
9. `Sales Order` kiem tra:
   - credit limit
   - cong no qua han
   - ton kha dung
   - so ngay han dung toi thieu theo item/customer
10. Neu thieu hang:
   - tao `Material Request`
   - hoac dua vao `Production Plan`
11. Kho tao `Pick List` theo FEFO.
12. He thong chi cho pick tu kho `Released`.
13. Tao `Delivery Note`, gan batch cho tung dong hang.
14. Tao `Sales Invoice`.
15. Tich hop e-invoice va nhan so hoa don.
16. Thu tien qua `Payment Entry` hoac doi soat ngan hang.
17. Neu tra hang:
   - tao `Sales Return`
   - tao `Credit Note`

## 3. B2C sales flow

1. Website/app gui order vao API ERPNext.
2. ERP tao `Customer` theo email/so dien thoai hoac map khach cu.
3. He thong tinh ton kha dung theo kho fulfillment.
4. Tao `Sales Order`.
5. Tao `Payment Request` sang gateway.
6. Nhan callback thanh cong:
   - cap nhat order
   - tao `Payment Entry`
7. Kho xu ly pick-pack-ship.
8. Tao `Sales Invoice`.
9. Dong bo trang thai giao hang ve website/app.

## 4. Business rules dac thu duoc

- Chi cho xuat hang tu batch `Released`.
- Chan xuat neu `expiry_date - posting_date < min_remaining_shelf_life_days`.
- Neu item yeu cau bao quan lanh, chi cho chon kho co `cold_chain_enabled`.
- Don hang cua benh vien co the yeu cau batch/lot traceability tren chung tu giao.

## 5. Ngoai le va tinh huong can xu ly

- Khach vuot credit limit: block submit va gui Finance phe duyet.
- Batch co temperature excursion: hold batch, khong cho pick.
- Khach yeu cau doi batch: tao amendment co audit trail.
- Recall sau giao hang: khoi tao `PH Recall Case`, truy vet tu Delivery Note va Sales Invoice.

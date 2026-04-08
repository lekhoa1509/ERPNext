# pharma_vn

Custom ERPNext/Frappe app cho doanh nghiep duoc tai Viet Nam.

## Scope

- Batch release truoc khi xuat ban.
- Temperature log va cold-chain alert.
- Recall case va batch traceability.
- API cho order, stock, payment gateway, IoT.
- Automation cho Purchase Receipt va Delivery Note.

## Cai dat vao bench hien co

```bash
bench get-app /path/to/this/repo/apps/pharma_vn
bench --site your-site install-app pharma_vn
```

## Sau khi cai dat

1. Tao roles va users theo tai lieu.
2. Chay migrate.
3. Cau hinh custom fields, workflow, scheduler.
4. Ket noi website, WMS, payment gateway, e-invoice.

## Ghi chu

- Day la skeleton custom app, khong phai full bench.
- Nen trien khai cung ERPNext/ERPNext app trong mot bench rieng.


# Integration Design

## 1. Nguyen tac

- ERPNext la source of truth cho order, inventory, AR/AP, GL.
- He thong ngoai chi dong vai tro channel hoac execution endpoint.
- Tich hop qua REST API va webhook, tranh ghi truc tiep vao database.

## 2. Danh sach API de xay dung

| API | Chuc nang |
| --- | --- |
| `POST /api/method/pharma_vn.api.orders.create_b2b_order` | Tao Sales Order tu CRM/DMS |
| `GET /api/method/pharma_vn.api.stock.get_sellable_stock` | Lay ton kha dung da release theo item/kho |
| `POST /api/method/pharma_vn.api.payments.vnpay_callback` | Nhan callback thanh toan |
| `POST /api/method/pharma_vn.api.quality.release_batch` | Release/hold batch |
| `POST /api/method/pharma_vn.api.integrations.log_temperature` | Nhan nhiet do tu IoT |
| `POST /api/method/pharma_vn.api.integrations.trigger_recall` | Khoi tao recall |

## 3. Website va mobile app

### Luong du lieu

1. ERPNext dong bo master:
   - item
   - gia
   - kho ban
   - ton kha dung
2. Website tao gio hang va order.
3. Order day vao ERPNext.
4. ERPNext phan bo kho va tao Sales Order.
5. Trang thai thanh toan/giao hang tra nguoc lai website.

### Luu y

- Chi dong bo ton `Released`.
- Khong expose ton `Quarantine`, `Rejected`, `Hold`.

## 4. Payment gateway

### Luong du lieu

1. ERPNext tao payment request.
2. Gateway nhan request.
3. Khach thanh toan.
4. Gateway callback vao ERPNext.
5. ERPNext xac thuc checksum.
6. Tao `Payment Entry`.
7. Cap nhat trang thai invoice/order.

## 5. WMS/handheld

### Luong du lieu

1. ERPNext tao lenh pick.
2. WMS/handheld nhan list can lay.
3. Nhan vien scan vi tri, item, batch.
4. WMS gui ket qua ve ERPNext.
5. ERPNext tao/hoan tat `Delivery Note` hoac `Stock Entry`.

## 6. CRM/DMS

- CRM quan ly lead va hoat dong pre-sales.
- DMS quan ly sales rep mobile.
- ERPNext quan ly quotation, gia, ton, credit, invoice, cong no.

## 7. IoT va cold-chain

- Cam bien gui log nhiet do theo chu ky.
- ERPNext tao `PH Temperature Log`.
- Neu vuot nguong:
  - gui alert
  - danh dau batch co lien quan la `Hold`

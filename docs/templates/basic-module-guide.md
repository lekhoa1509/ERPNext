# Basic Module Guide

## 1. Muc tieu

Tai lieu nay huong dan cach tao module co ban nhat cho app `pharma_vn` trong repo nay.

Sau khi lam xong, ban se co:

- `1` module moi trong app
- `1` DocType custom don gian
- co the `migrate` va thay duoc tren ERPNext/Frappe

Vi du trong tai lieu nay dung:

- Module: `Basic Ops`
- Python package: `basic_ops`
- DocType: `BO Note`

## 2. Khi nao can tao module moi

Tao module moi khi:

- nhom chuc nang co domain rieng, tach biet voi `HRM`, `Pharma Operations`, `Dynamic Forms`
- can gom DocType, API, workspace va logic vao mot khu ro rang
- du kien se mo rong tiep trong tuong lai

Khong can tao module moi khi:

- chi them `1-2` field nho vao flow da co
- chi them `1` helper/service nho cho module hien huu
- logic van thuoc ro rang vao mot module dang ton tai

## 3. Cau truc toi thieu

Module co ban nhat trong repo nay thuong co:

```text
apps/pharma_vn/pharma_vn/basic_ops/
apps/pharma_vn/pharma_vn/basic_ops/__init__.py
apps/pharma_vn/pharma_vn/basic_ops/doctype/
apps/pharma_vn/pharma_vn/basic_ops/doctype/__init__.py
apps/pharma_vn/pharma_vn/basic_ops/doctype/bo_note/
apps/pharma_vn/pharma_vn/basic_ops/doctype/bo_note/__init__.py
apps/pharma_vn/pharma_vn/basic_ops/doctype/bo_note/bo_note.py
apps/pharma_vn/pharma_vn/basic_ops/doctype/bo_note/bo_note.json
```

Bat buoc phai co:

- ten module trong `apps/pharma_vn/pharma_vn/modules.txt`
- package Python cua module
- thu muc `doctype`
- file `.json` cua DocType
- file `.py` cua DocType

## 4. Buoc 0: bat developer mode

Frappe can `developer_mode` de khi tao DocType, framework sinh file vao app de dua vao git.

Chay trong bench:

```bash
bench set-config -g developer_mode true
```

Neu dang chay local dev:

```bash
bench start
```

Neu dang chay bang Docker, thuc hien trong container `backend`.

## 5. Buoc 1: them module vao app

Mo file:

- `apps/pharma_vn/pharma_vn/modules.txt`

Them dong moi:

```text
Basic Ops
```

Quy uoc:

- ten hien thi trong `modules.txt` la ten nguoi dung nhin thay
- ten thu muc package nen o dang snake_case, vi du `basic_ops`
- xem them quy uoc tai `docs/templates/naming-convention.md`

## 6. Buoc 2: tao package module

Tao cau truc thu muc:

```text
apps/pharma_vn/pharma_vn/basic_ops/
apps/pharma_vn/pharma_vn/basic_ops/doctype/
```

Tao file:

```python
# apps/pharma_vn/pharma_vn/basic_ops/__init__.py
```

```python
# apps/pharma_vn/pharma_vn/basic_ops/doctype/__init__.py
```

Hai file nay co the de trong. Muc dich cua buoc nay la de package Python ton tai ro rang truoc khi tao DocType.

## 7. Buoc 3: tao DocType don gian nhat

Cach de nhat va dung voi Frappe la tao DocType tren Desk khi `developer_mode` da bat.

### 7.1. Chon ten

Vi du:

- DocType label: `BO Note`
- doctype folder: `bo_note`
- Python class: `BONote`

### 7.2. Tao DocType tren Desk

Trong ERPNext/Frappe:

1. Mo Awesome Bar
2. Tim `DocType`
3. Bam `New`
4. Nhap:
   - Name: `BO Note`
   - Module: `Basic Ops`
5. Bo chon `Custom?`
6. Them `2` field:
   - `Title` - type `Data` - Mandatory
   - `Note` - type `Small Text`
7. Save

Khi save xong, Frappe se sinh cac file code vao app neu site dang o `developer_mode`.

### 7.3. Cac file framework se tao

Sau khi save, ban thuong se thay:

```text
apps/pharma_vn/pharma_vn/basic_ops/doctype/bo_note/__init__.py
apps/pharma_vn/pharma_vn/basic_ops/doctype/bo_note/bo_note.json
apps/pharma_vn/pharma_vn/basic_ops/doctype/bo_note/bo_note.py
apps/pharma_vn/pharma_vn/basic_ops/doctype/bo_note/bo_note.js
apps/pharma_vn/pharma_vn/basic_ops/doctype/bo_note/test_bo_note.py
```

### 7.4. File Python toi thieu

File:

```python
# apps/pharma_vn/pharma_vn/basic_ops/doctype/bo_note/bo_note.py

import frappe
from frappe.model.document import Document


class BONote(Document):
    pass
```

### 7.5. Tao file `__init__.py`

File:

```python
# apps/pharma_vn/pharma_vn/basic_ops/doctype/bo_note/__init__.py
```

### 7.6. Mau JSON tham khao

Thong thuong ban khong can viet tay file JSON neu tao DocType bang Desk. Doan duoi day chi la mau de ban hieu cau truc framework sinh ra:

File:

```json
{
  "actions": [],
  "allow_copy": 0,
  "allow_events_in_timeline": 0,
  "allow_guest_to_view": 0,
  "allow_import": 0,
  "allow_rename": 0,
  "autoname": "format:BO-.YYYY.-.#####",
  "creation": "2026-04-10 00:00:00.000000",
  "custom": 0,
  "docstatus": 0,
  "doctype": "DocType",
  "editable_grid": 1,
  "engine": "InnoDB",
  "field_order": [
    "title",
    "note"
  ],
  "fields": [
    {
      "fieldname": "title",
      "fieldtype": "Data",
      "in_list_view": 1,
      "label": "Title",
      "reqd": 1
    },
    {
      "fieldname": "note",
      "fieldtype": "Small Text",
      "label": "Note"
    }
  ],
  "grid_page_length": 50,
  "index_web_pages_for_search": 1,
  "istable": 0,
  "links": [],
  "modified": "2026-04-10 00:00:00.000000",
  "modified_by": "Administrator",
  "module": "Basic Ops",
  "name": "BO Note",
  "naming_rule": "Expression",
  "owner": "Administrator",
  "permissions": [
    {
      "create": 1,
      "delete": 1,
      "email": 1,
      "export": 1,
      "print": 1,
      "read": 1,
      "report": 1,
      "role": "System Manager",
      "share": 1,
      "write": 1
    }
  ],
  "quick_entry": 1,
  "row_format": "Dynamic",
  "sort_field": "modified",
  "sort_order": "DESC",
  "states": [],
  "track_changes": 1
}
```

DocType nay la muc toi thieu de test:

- tao ban ghi duoc
- co `Title`
- co `Note`
- co naming series co ban
- chi `System Manager` duoc thao tac

## 8. Buoc 4: migrate va sync metadata

Trong bench dang cai app `pharma_vn`, chay:

```bash
bench --site your-site migrate
```

Neu ban tao DocType dung cach trong `developer_mode` va bo chon `Custom?`, file code da duoc sinh vao app, nen thuong chi can `migrate` roi commit code.

Neu repo nay dang chay bang Docker, thuc hien trong container `backend`.

## 9. Buoc 5: kiem tra tren ERPNext

Sau khi migrate, kiem tra:

1. Vao Awesome Bar, go `BO Note`
2. Mo list view cua `BO Note`
3. Tao thu `1` record moi
4. Kiem tra record duoc luu va co series dang `BO-2026-00001`

Neu khong tim thay DocType:

- kiem tra `modules.txt` da co `Basic Ops` chua
- kiem tra truong `"module": "Basic Ops"` trong file JSON
- kiem tra da `migrate` dung site chua
- kiem tra app `pharma_vn` da duoc install vao site chua

## 10. Buoc 6: neu muon hien tren Desk

Module co the da ton tai nhung chua co icon/workspace tren Desk. Cach don gian:

- tao Workspace cho module
- hoac them vao custom desktop shell cua repo nay

Nhung voi muc tieu "co ban nhat", ban chua can lam workspace ngay.

## 11. Checklist nhanh

- them module vao `modules.txt`
- tao package snake_case cho module
- bat `developer_mode`
- tao `doctype/<doctype_name>/`
- kiem tra `__init__.py`
- kiem tra `<doctype_name>.py`
- kiem tra `<doctype_name>.json`
- dat `"module"` trong JSON dung voi ten trong `modules.txt`
- chay `bench --site your-site migrate`
- vao ERPNext tao thu `1` record

## 12. Goi y dat ten theo repo nay

Nen uu tien:

- module label: ngan, ro domain, vi du `Basic Ops`, `Cold Chain`, `QA Control`
- package: snake_case, vi du `basic_ops`, `cold_chain`, `qa_control`
- DocType custom: co prefix ro rang, vi du `BO Note`, `PH CAPA`, `WH Cell`

Trong repo hien tai, ban co the tham khao module da co:

- `apps/pharma_vn/pharma_vn/pharma_operations/`
- `apps/pharma_vn/pharma_vn/hrm/`
- `apps/pharma_vn/pharma_vn/dynamic_forms/`
- `apps/pharma_vn/pharma_vn/warehouse_layout_2d/`

## 13. Muc mo rong tiep theo

Sau khi module co ban da chay, thuong se mo rong theo thu tu:

1. them validation trong file `.py`
2. them workspace
3. them API trong `pharma_vn.api.*`
4. them automation/hook
5. them test unit

Neu can nhanh, co the xem tai lieu nay nhu "khung xuat phat" cho moi module moi trong `pharma_vn`.

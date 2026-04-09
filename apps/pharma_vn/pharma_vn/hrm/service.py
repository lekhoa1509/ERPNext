import json

import frappe
from frappe.utils import nowdate


HRM_RECORD_TABLE = "tabPH HRM Record"

PAGE_META = {
    "hrm-dashboard": {"label": "Dashboard", "title": "HRM Dashboard", "icon": "home"},
    "hrm-reports": {"label": "Bao cao", "title": "Báo cáo", "icon": "bar-chart-2"},
    "hrm-employee-profile": {"label": "Ho so nhan su", "title": "Hồ sơ nhân sự", "icon": "users", "title_field": "full_name"},
    "hrm-contracts": {"label": "Hop dong", "title": "Hợp đồng", "icon": "file-text", "title_field": "contract_title"},
    "hrm-attendance": {"label": "Cham cong", "title": "Chấm công", "icon": "clock", "title_field": "attendance_title"},
    "hrm-leave": {"label": "Nghi phep", "title": "Nghỉ phép", "icon": "calendar", "title_field": "leave_title"},
    "hrm-payroll": {"label": "Tinh luong", "title": "Tính lương", "icon": "wallet", "title_field": "payroll_title"},
    "hrm-performance": {"label": "Danh gia", "title": "Đánh giá", "icon": "target", "title_field": "review_title"},
    "hrm-kpi": {"label": "KPI", "title": "KPI", "icon": "trending-up", "title_field": "kpi_title"},
    "hrm-meeting-room-booking": {"label": "Book phong hop", "title": "Book phòng họp", "icon": "building", "title_field": "booking_title"},
    "hrm-document-archive": {"label": "Luu ho so", "title": "Lưu hồ sơ", "icon": "archive", "title_field": "document_title"},
    "hrm-offboarding": {"label": "Nghi viec", "title": "Nghỉ việc", "icon": "log-out", "title_field": "offboarding_title"},
}
NON_RECORD_PAGE_KEYS = {"hrm-dashboard", "hrm-reports"}


def ensure_hrm_schema():
    frappe.db.sql(
        f"""
        CREATE TABLE IF NOT EXISTS `{HRM_RECORD_TABLE}` (
            `name` varchar(140) NOT NULL,
            `page_key` varchar(140) NOT NULL,
            `title` varchar(255) DEFAULT NULL,
            `status` varchar(140) DEFAULT NULL,
            `subject` varchar(255) DEFAULT NULL,
            `employee_code` varchar(140) DEFAULT NULL,
            `employee_name` varchar(255) DEFAULT NULL,
            `company` varchar(255) DEFAULT NULL,
            `posting_date` date DEFAULT NULL,
            `start_date` date DEFAULT NULL,
            `end_date` date DEFAULT NULL,
            `amount` decimal(18,2) DEFAULT 0,
            `file_url` text DEFAULT NULL,
            `payload_json` longtext DEFAULT NULL,
            `owner` varchar(140) DEFAULT NULL,
            `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
            `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (`name`),
            KEY `page_key` (`page_key`),
            KEY `updated_at` (`updated_at`)
        ) ENGINE=InnoDB ROW_FORMAT=DYNAMIC CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )


def ensure_hrm_setup():
    ensure_hrm_schema()
    ensure_hrm_module()
    ensure_hrm_pages()
    ensure_hrm_workspace()
    ensure_hrm_sidebar()
    ensure_hrm_desktop_icon()


def ensure_hrm_module():
    if frappe.db.exists("Module Def", "HRM"):
        return
    frappe.get_doc(
        {
            "doctype": "Module Def",
            "name": "HRM",
            "module_name": "HRM",
            "app_name": "pharma_vn",
            "custom": 0,
        }
    ).insert(ignore_permissions=True)


def ensure_hrm_pages():
    for page_name, meta in PAGE_META.items():
        if frappe.db.exists("Page", page_name):
            continue
        frappe.get_doc(
            {
                "doctype": "Page",
                "name": page_name,
                "page_name": page_name,
                "title": meta["title"],
                "module": "HRM",
                "icon": meta["icon"],
                "standard": "Yes",
            }
        ).insert(ignore_permissions=True)


def ensure_hrm_workspace():
    shortcuts = []
    links = [
        {
            "label": "HRM",
            "type": "Card Break",
            "link_type": "Page",
            "description": "Custom pages for HRM without business DocTypes.",
            "link_count": len(PAGE_META),
            "hidden": 0,
            "is_query_report": 0,
            "onboard": 0,
        }
    ]
    for page_name, meta in PAGE_META.items():
        shortcuts.append(
            {
                "label": meta["title"],
                "link_to": page_name,
                "type": "Page",
                "color": "Blue",
                "doc_view": "List",
                "stats_filter": "[]",
            }
        )
        links.append(
            {
                "label": meta["title"],
                "link_to": page_name,
                "link_type": "Page",
                "type": "Link",
                "hidden": 0,
                "is_query_report": 0,
                "onboard": 0,
                "link_count": 0,
            }
        )

    if frappe.db.exists("Workspace", "HRM"):
        workspace = frappe.get_doc("Workspace", "HRM")
        workspace.module = "HRM"
        workspace.label = "HRM"
        workspace.title = "HRM"
        workspace.icon = "users"
        workspace.public = 1
        workspace.links = []
        workspace.shortcuts = []
    else:
        workspace = frappe.get_doc(
            {
                "doctype": "Workspace",
                "name": "HRM",
                "module": "HRM",
                "label": "HRM",
                "title": "HRM",
                "icon": "users",
                "public": 1,
            }
        )

    workspace.set("links", links)
    workspace.set("shortcuts", shortcuts)
    workspace.content = frappe.as_json(
        [
            {"id": f"shortcut_{idx}", "type": "shortcut", "data": {"shortcut_name": item["label"], "col": 3}}
            for idx, item in enumerate(shortcuts, start=1)
        ]
    )
    workspace.save(ignore_permissions=True)


def ensure_hrm_sidebar():
    items = [
        {
            "label": "HRM",
            "link_to": "HRM",
            "link_type": "Workspace",
            "type": "Link",
            "icon": "layout-dashboard",
            "indent": 0,
            "child": 0,
            "collapsible": 1,
            "keep_closed": 0,
            "show_arrow": 0,
        }
    ]
    for page_name, meta in PAGE_META.items():
        items.append(
            {
                "label": meta["title"],
                "link_to": page_name,
                "link_type": "Page",
                "type": "Link",
                "icon": meta["icon"],
                "indent": 0,
                "child": 0,
                "collapsible": 1,
                "keep_closed": 0,
                "show_arrow": 0,
            }
        )

    if frappe.db.exists("Workspace Sidebar", "HRM"):
        sidebar = frappe.get_doc("Workspace Sidebar", "HRM")
    else:
        sidebar = frappe.get_doc({"doctype": "Workspace Sidebar", "name": "HRM"})

    sidebar.module = "HRM"
    sidebar.title = "HRM"
    sidebar.header_icon = "users"
    sidebar.set("items", items)
    sidebar.save(ignore_permissions=True)


def ensure_hrm_desktop_icon():
    if frappe.db.exists("Desktop Icon", "HRM"):
        icon = frappe.get_doc("Desktop Icon", "HRM")
    else:
        icon = frappe.get_doc({"doctype": "Desktop Icon", "name": "HRM"})

    icon.label = "HRM"
    icon.icon = "users"
    icon.icon_type = "Link"
    icon.link_type = "Workspace Sidebar"
    icon.link_to = "HRM"
    icon.standard = 1
    icon.hidden = 0
    icon.save(ignore_permissions=True)


def get_allowed_page_keys():
    return [key for key in PAGE_META if key not in NON_RECORD_PAGE_KEYS]


def validate_page_key(page_key):
    if page_key not in PAGE_META:
        frappe.throw(f"Unsupported HRM page: {page_key}")


def get_record_name(page_key):
    slug = page_key.replace("hrm-", "").replace("-", "_").upper()
    return f"HRM-{slug}-{nowdate().replace('-', '')}-{frappe.generate_hash(length=6).upper()}"


def normalize_payload(page_key, payload):
    validate_page_key(page_key)
    payload = frappe._dict(payload or {})
    title_field = PAGE_META[page_key].get("title_field")
    title = payload.get(title_field) or payload.get("title") or payload.get("employee_name") or payload.get("full_name")
    status = payload.get("status")
    subject = payload.get("subject") or payload.get("notes") or title
    amount = payload.get("amount") or payload.get("net_salary") or payload.get("salary_amount") or 0
    return {
        "title": title,
        "status": status,
        "subject": subject,
        "employee_code": payload.get("employee_code"),
        "employee_name": payload.get("employee_name") or payload.get("full_name"),
        "company": payload.get("company"),
        "posting_date": payload.get("posting_date") or payload.get("effective_date") or payload.get("booking_date"),
        "start_date": payload.get("start_date") or payload.get("join_date") or payload.get("contract_start"),
        "end_date": payload.get("end_date") or payload.get("contract_end") or payload.get("last_working_date"),
        "amount": amount,
        "file_url": payload.get("file_url"),
        "payload_json": json.dumps(payload, ensure_ascii=True),
    }


def deserialize_record(row):
    payload = {}
    if row.payload_json:
        payload = frappe.parse_json(row.payload_json) or {}
    payload.update(
        {
            "name": row.name,
            "page_key": row.page_key,
            "title": row.title,
            "status": row.status,
            "employee_code": row.employee_code,
            "employee_name": row.employee_name,
            "company": row.company,
            "posting_date": str(row.posting_date) if row.posting_date else "",
            "start_date": str(row.start_date) if row.start_date else "",
            "end_date": str(row.end_date) if row.end_date else "",
            "amount": float(row.amount or 0),
            "file_url": row.file_url or "",
            "updated_at": str(row.updated_at) if row.updated_at else "",
        }
    )
    return payload

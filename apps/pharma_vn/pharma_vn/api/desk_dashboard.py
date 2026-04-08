import frappe
from frappe.utils import add_days, format_datetime, formatdate, getdate, now_datetime, nowdate


SUMMARY_SPECS = [
    {
        "key": "item_master",
        "label": "Item Master",
        "doctype": "Item",
        "mode": "all",
        "hint": "Master data is ready for import.",
    },
    {
        "key": "customer_master",
        "label": "Customer Master",
        "doctype": "Customer",
        "mode": "all",
        "hint": "Customer records currently managed in the system.",
    },
    {
        "key": "sales_30d",
        "label": "Sales Orders (30 Days)",
        "doctype": "Sales Order",
        "mode": "period",
        "date_field": "transaction_date",
        "hint": "Sales order volume posted in the last 30 days.",
    },
    {
        "key": "purchase_30d",
        "label": "Purchase Orders (30 Days)",
        "doctype": "Purchase Order",
        "mode": "period",
        "date_field": "transaction_date",
        "hint": "Purchase order volume posted in the last 30 days.",
    },
]

TIMELINE_SPECS = [
    {
        "doctype": "Sales Order",
        "label": "Sales Orders",
        "date_field": "transaction_date",
        "color": "#67e1c7",
    },
    {
        "doctype": "Purchase Order",
        "label": "Purchase Orders",
        "date_field": "transaction_date",
        "color": "#5aa8ff",
    },
    {
        "doctype": "Sales Invoice",
        "label": "Sales Invoices",
        "date_field": "posting_date",
        "color": "#9a8cff",
    },
]

WORKLOAD_SPECS = [
    {
        "label": "SO chờ duyệt",
        "doctype": "Sales Order",
        "filters": {"docstatus": 0},
        "hint": "Draft orders or orders pending internal approval.",
    },
    {
        "label": "DN chờ submit",
        "doctype": "Delivery Note",
        "filters": {"docstatus": 0},
        "hint": "Delivery notes are being prepared for dispatch.",
    },
    {
        "label": "PO đang mở",
        "doctype": "Purchase Order",
        "filters": {"docstatus": ["<", 2], "status": ["not in", ["Completed", "Closed", "Cancelled"]]},
        "hint": "Purchase orders are not yet completed or closed.",
    },
    {
        "label": "PR chờ nhập",
        "doctype": "Purchase Receipt",
        "filters": {"docstatus": 0},
        "hint": "Purchase receipts are waiting in the intake preparation step.",
    },
]

RECENT_SPECS = [
    {
        "doctype": "Sales Order",
        "label": "Sales Orders",
        "date_field": "transaction_date",
        "party_field": "customer",
    },
    {
        "doctype": "Purchase Order",
        "label": "Purchase Orders",
        "date_field": "transaction_date",
        "party_field": "supplier",
    },
    {
        "doctype": "Sales Invoice",
        "label": "Sales Invoices",
        "date_field": "posting_date",
        "party_field": "customer",
    },
    {
        "doctype": "Purchase Receipt",
        "label": "Purchase Receipts",
        "date_field": "posting_date",
        "party_field": "supplier",
    },
]

HIGHLIGHT_SPECS = [
    {
        "label": "Warehouses",
        "doctype": "Warehouse",
        "hint": "Warehouse structure and storage locations are ready.",
    },
    {
        "label": "Accounts",
        "doctype": "Account",
        "hint": "Foundational finance setup for accounting and reconciliation.",
    },
    {
        "label": "Sales Taxes",
        "doctype": "Sales Taxes and Charges Template",
        "hint": "Sales tax templates are available for orders and invoices.",
    },
    {
        "label": "Purchase Taxes",
        "doctype": "Purchase Taxes and Charges Template",
        "hint": "Purchase tax templates are available for import and matching.",
    },
]


@frappe.whitelist()
def get_desk_dashboard():
    today = getdate(nowdate())
    timeline_days = 14
    timeline_start = add_days(today, -(timeline_days - 1))
    timeline_labels = [formatdate(add_days(timeline_start, offset), "dd MMM") for offset in range(timeline_days)]

    summary_cards = [_build_summary_card(spec, today) for spec in SUMMARY_SPECS]
    timeline = {
        "labels": timeline_labels,
        "series": [_build_timeline_series(spec, timeline_start, today, timeline_days) for spec in TIMELINE_SPECS],
    }
    workload = [_build_workload_item(spec) for spec in WORKLOAD_SPECS]
    recent_documents = _get_recent_documents(limit=6)
    highlights = [_build_highlight(spec) for spec in HIGHLIGHT_SPECS]

    is_fresh_site = not any(card["value"] for card in summary_cards[2:]) and not recent_documents
    hero_note = (
        "Site is currently in a clean data state. Import masters and transactions for the dashboard to reflect live operations."
        if is_fresh_site
        else "Track sales, purchasing, and recent transactions in one command center."
    )

    return {
        "ok": True,
        "generated_at_label": format_datetime(now_datetime(), "dd MMM yyyy, HH:mm"),
        "hero_note": frappe._(hero_note),
        "summary_cards": summary_cards,
        "timeline": timeline,
        "workload": workload,
        "recent_documents": recent_documents,
        "highlights": highlights,
    }


def _build_summary_card(spec, today):
    value = 0
    if _can_read(spec["doctype"]):
        if spec["mode"] == "all":
            value = frappe.db.count(spec["doctype"])
        else:
            start_date = add_days(today, -29)
            value = frappe.db.count(
                spec["doctype"], filters={spec["date_field"]: ["between", [start_date, today]]}
            )

    return {
        "key": spec["key"],
        "label": frappe._(spec["label"]),
        "value": value,
        "hint": frappe._(spec["hint"]),
        "sparkline": _get_weekly_counts(spec["doctype"], weeks=8),
    }


def _build_timeline_series(spec, start_date, end_date, total_days):
    values = [0] * total_days
    if _can_read(spec["doctype"]):
        rows = frappe.get_all(
            spec["doctype"],
            filters={spec["date_field"]: ["between", [start_date, end_date]]},
            fields=[spec["date_field"]],
            limit_page_length=0,
            order_by=f"{spec['date_field']} asc",
        )
        for row in rows:
            row_date = row.get(spec["date_field"])
            if not row_date:
                continue
            index = (getdate(row_date) - getdate(start_date)).days
            if 0 <= index < total_days:
                values[index] += 1

    return {
        "name": frappe._(spec["label"]),
        "color": spec["color"],
        "values": values,
    }


def _build_workload_item(spec):
    value = _safe_count(spec["doctype"], spec["filters"])
    return {
        "label": frappe._(spec["label"]),
        "value": value,
        "hint": frappe._(spec["hint"]),
    }


def _build_highlight(spec):
    return {
        "label": frappe._(spec["label"]),
        "value": _safe_count(spec["doctype"]),
        "hint": frappe._(spec["hint"]),
    }


def _get_recent_documents(limit=6):
    rows = []
    for spec in RECENT_SPECS:
        if not _can_read(spec["doctype"]):
            continue

        fields = ["name", "status", "modified", spec["date_field"], spec["party_field"]]
        entries = frappe.get_all(
            spec["doctype"],
            fields=fields,
            limit_page_length=limit,
            order_by="modified desc",
        )
        for entry in entries:
            rows.append(
                {
                    "doctype": spec["doctype"],
                    "doctype_label": frappe._(spec["label"]),
                    "name": entry.name,
                    "status": entry.status or "Draft",
                    "date_label": formatdate(entry.get(spec["date_field"])) if entry.get(spec["date_field"]) else "",
                    "counterparty": entry.get(spec["party_field"]) or "",
                    "modified": entry.modified,
                }
            )

    rows.sort(key=lambda row: row.get("modified") or "", reverse=True)
    return rows[:limit]


def _get_weekly_counts(doctype, weeks=8):
    if not _can_read(doctype):
        return [0] * weeks

    start_date = add_days(getdate(nowdate()), -((weeks * 7) - 1))
    counts = [0] * weeks
    rows = frappe.get_all(
        doctype,
        fields=["creation"],
        filters={"creation": [">=", start_date]},
        limit_page_length=0,
        order_by="creation asc",
    )
    for row in rows:
        if not row.creation:
            continue
        index = (getdate(row.creation) - start_date).days // 7
        if 0 <= index < weeks:
            counts[index] += 1

    return counts


def _safe_count(doctype, filters=None):
    if not _can_read(doctype):
        return 0
    return frappe.db.count(doctype, filters or {})


def _can_read(doctype):
    return frappe.has_permission(doctype, "read")

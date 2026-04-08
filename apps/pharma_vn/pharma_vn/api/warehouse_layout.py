import json

import frappe
from frappe import _
from frappe.utils import flt

from pharma_vn.utils.response import ok
from pharma_vn.warehouse_layout_2d.service import get_layout_overview


@frappe.whitelist()
def get_layout(layout_name=None):
    layout_name = layout_name or frappe.form_dict.get("layout_name")
    if not layout_name:
        frappe.throw(_("layout_name is required"))

    return ok(_("Warehouse layout loaded"), get_layout_overview(layout_name))


@frappe.whitelist()
def get_active_layouts(warehouses=None):
    warehouses = warehouses or frappe.form_dict.get("warehouses") or []
    if isinstance(warehouses, str):
        try:
            warehouses = json.loads(warehouses)
        except json.JSONDecodeError:
            warehouses = [warehouse.strip() for warehouse in warehouses.split(",") if warehouse.strip()]

    warehouses = [warehouse for warehouse in warehouses if warehouse]
    if not warehouses:
        return ok(_("No warehouses provided"), {"layouts_by_warehouse": {}})

    layout_rows = frappe.get_all(
        "WH Layout",
        filters={
            "warehouse": ["in", warehouses],
            "is_active": 1,
        },
        fields=["name", "layout_name", "warehouse"],
        order_by="modified desc",
        limit_page_length=0,
    )

    layouts_by_warehouse = {}
    for row in layout_rows:
        if row.warehouse not in layouts_by_warehouse:
            layouts_by_warehouse[row.warehouse] = {
                "name": row.name,
                "layout_name": row.layout_name,
                "warehouse": row.warehouse,
            }

    return ok(_("Active warehouse layouts loaded"), {"layouts_by_warehouse": layouts_by_warehouse})


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def search_pickable_cells(doctype, txt, searchfield, start, page_len, filters):
    filters = filters or {}
    warehouse = filters.get("warehouse")
    layout = filters.get("layout")
    item_code = filters.get("item_code")
    required_qty = flt(filters.get("required_qty"))
    batch_no = filters.get("batch_no")

    if not warehouse or not item_code:
        return []

    cell_filters = {"warehouse": warehouse, "status": ["!=", "Blocked"]}
    if layout:
        cell_filters["layout"] = layout

    cells = frappe.get_all(
        "WH Cell",
        filters=cell_filters,
        fields=["name", "cell_code", "cell_label", "layout", "warehouse"],
        limit_page_length=0,
        order_by="cell_code asc, name asc",
    )
    if not cells:
        return []

    search_text = (txt or "").strip().lower()
    results = []
    for cell in cells:
        stock_filters = {
            "warehouse": warehouse,
            "cell": cell.name,
            "item_code": item_code,
        }
        if batch_no:
            stock_filters["batch_no"] = batch_no

        stock_rows = frappe.get_all(
            "WH Cell Stock",
            filters=stock_filters,
            fields=["qty", "uom"],
            limit_page_length=0,
        )
        available_qty = sum(flt(row.qty) for row in stock_rows)
        if required_qty and available_qty + 0.0001 < required_qty:
            continue

        label = f"{cell.cell_code or cell.name} {cell.cell_label or ''}".strip()
        if search_text and search_text not in label.lower() and search_text not in (cell.name or "").lower():
            continue

        results.append(
            (
                cell.name,
                f"{cell.cell_code or cell.name} - {cell.cell_label or ''}".strip(" -"),
                f"{available_qty:g} {(stock_rows[0].uom if stock_rows else '')}".strip(),
            )
        )

    return results[start : start + page_len]

import frappe
from frappe import _
from frappe.utils import cint, flt, now_datetime


def build_cell_code(row_index, column_index):
    return f"{_row_label(row_index)}{cint(column_index)}"


def build_cell_label(row_index, column_index):
    return _("Row {0} - Column {1}").format(_row_label(row_index), cint(column_index))


def sync_layout_cells(layout_doc):
    total_rows = cint(layout_doc.total_rows)
    total_columns = cint(layout_doc.total_columns)
    if total_rows <= 0 or total_columns <= 0:
        return

    existing_cells = {
        (cint(cell.row_index), cint(cell.column_index)): cell
        for cell in frappe.get_all(
            "WH Cell",
            filters={"layout": layout_doc.name},
            fields=["name", "row_index", "column_index", "warehouse", "cell_code", "cell_label"],
            limit_page_length=0,
        )
    }

    for row_index in range(1, total_rows + 1):
        for column_index in range(1, total_columns + 1):
            existing = existing_cells.get((row_index, column_index))
            if existing:
                updates = {}
                if layout_doc.warehouse and existing.warehouse != layout_doc.warehouse:
                    updates["warehouse"] = layout_doc.warehouse
                if not existing.cell_code:
                    updates["cell_code"] = build_cell_code(row_index, column_index)
                if not existing.cell_label:
                    updates["cell_label"] = build_cell_label(row_index, column_index)
                if updates:
                    frappe.db.set_value("WH Cell", existing.name, updates, update_modified=False)
                continue

            frappe.get_doc(
                {
                    "doctype": "WH Cell",
                    "layout": layout_doc.name,
                    "warehouse": layout_doc.warehouse,
                    "row_index": row_index,
                    "column_index": column_index,
                    "cell_code": build_cell_code(row_index, column_index),
                    "cell_label": build_cell_label(row_index, column_index),
                    "status": "Available",
                }
            ).insert(ignore_permissions=True)


def get_layout_overview(layout_name):
    layout_doc = frappe.get_doc("WH Layout", layout_name)
    sync_layout_cells(layout_doc)

    cells = frappe.get_all(
        "WH Cell",
        filters={"layout": layout_doc.name},
        fields=[
            "name",
            "cell_code",
            "cell_label",
            "row_index",
            "column_index",
            "status",
            "capacity_qty",
            "notes",
        ],
        order_by="row_index asc, column_index asc",
        limit_page_length=0,
    )

    stock_rows = frappe.get_all(
        "WH Cell Stock",
        filters={"layout": layout_doc.name, "qty": (">", 0)},
        fields=["cell", "item_code", "batch_no", "qty", "uom", "last_movement_on"],
        order_by="cell asc, item_code asc, batch_no asc",
        limit_page_length=0,
    )

    stock_map = {}
    for stock_row in stock_rows:
        stock_map.setdefault(stock_row.cell, []).append(
            {
                "item_code": stock_row.item_code,
                "batch_no": stock_row.batch_no,
                "qty": flt(stock_row.qty),
                "uom": stock_row.uom,
                "last_movement_on": stock_row.last_movement_on,
            }
        )

    layout_cells = []
    for cell in cells:
        cell_stock_rows = stock_map.get(cell.name, [])
        total_qty = sum(flt(row["qty"]) for row in cell_stock_rows)
        layout_cells.append(
            {
                "name": cell.name,
                "cell_code": cell.cell_code,
                "cell_label": cell.cell_label,
                "row_index": cint(cell.row_index),
                "column_index": cint(cell.column_index),
                "status": cell.status,
                "capacity_qty": flt(cell.capacity_qty),
                "notes": cell.notes,
                "total_qty": total_qty,
                "item_count": len(cell_stock_rows),
                "stock_rows": cell_stock_rows,
            }
        )

    return {
        "layout": {
            "name": layout_doc.name,
            "layout_name": layout_doc.layout_name,
            "warehouse": layout_doc.warehouse,
            "company": layout_doc.company,
            "total_rows": cint(layout_doc.total_rows),
            "total_columns": cint(layout_doc.total_columns),
        },
        "cells": layout_cells,
    }


def validate_cell_assignment(cell_name, layout=None, warehouse=None):
    if not cell_name:
        return None

    cell = frappe.get_cached_value(
        "WH Cell",
        cell_name,
        ["name", "layout", "warehouse", "status", "cell_code"],
        as_dict=True,
    )
    if not cell:
        frappe.throw(_("Storage cell {0} does not exist").format(cell_name))

    if layout and cell.layout != layout:
        frappe.throw(
            _("Storage cell {0} does not belong to layout {1}").format(cell.cell_code or cell.name, layout)
        )

    if warehouse and cell.warehouse and cell.warehouse != warehouse:
        frappe.throw(
            _("Storage cell {0} does not belong to warehouse {1}").format(
                cell.cell_code or cell.name, warehouse
            )
        )

    if cell.status == "Blocked":
        frappe.throw(_("Storage cell {0} is blocked").format(cell.cell_code or cell.name))

    return cell


def warehouse_has_active_layout(warehouse):
    if not warehouse:
        return False

    return bool(
        frappe.db.exists(
            "WH Layout",
            {
                "warehouse": warehouse,
                "is_active": 1,
            },
        )
    )


def apply_cell_movement(
    *,
    cell_name,
    layout_name,
    warehouse,
    item_code,
    batch_no=None,
    qty_delta=0,
    uom=None,
    movement_type="Inbound",
    posting_datetime_value=None,
    source_doctype=None,
    source_name=None,
    source_row_name=None,
    remarks=None,
):
    qty_delta = flt(qty_delta)
    if not qty_delta:
        return

    matching_stock_rows = frappe.get_all(
        "WH Cell Stock",
        filters={"cell": cell_name, "item_code": item_code},
        fields=["name", "qty", "batch_no"],
        limit_page_length=0,
    )
    stock_row = next(
        (row for row in matching_stock_rows if (row.batch_no or "") == (batch_no or "")),
        None,
    )

    current_qty = flt(stock_row.qty) if stock_row else 0
    new_qty = current_qty + qty_delta
    if new_qty < -0.0001:
        frappe.throw(
            _("Cell stock for item {0} in cell {1} would become negative").format(item_code, cell_name)
        )
    new_qty = max(new_qty, 0)

    stock_values = {
        "layout": layout_name,
        "warehouse": warehouse,
        "cell": cell_name,
        "item_code": item_code,
        "batch_no": batch_no,
        "qty": new_qty,
        "uom": uom,
        "last_movement_on": posting_datetime_value or now_datetime(),
        "last_movement_type": movement_type,
    }

    if stock_row:
        frappe.db.set_value("WH Cell Stock", stock_row.name, stock_values, update_modified=False)
    else:
        frappe.get_doc({"doctype": "WH Cell Stock", **stock_values}).insert(ignore_permissions=True)

    frappe.get_doc(
        {
            "doctype": "WH Cell Movement",
            "posting_datetime": posting_datetime_value or now_datetime(),
            "movement_type": movement_type,
            "layout": layout_name,
            "warehouse": warehouse,
            "cell": cell_name,
            "item_code": item_code,
            "batch_no": batch_no,
            "qty_change": qty_delta,
            "balance_qty_after": new_qty,
            "uom": uom,
            "source_doctype": source_doctype,
            "source_name": source_name,
            "source_row_name": source_row_name,
            "remarks": remarks,
        }
    ).insert(ignore_permissions=True)


def _row_label(row_index):
    row_index = cint(row_index)
    if row_index <= 0:
        return "A"

    label = []
    while row_index:
        row_index, remainder = divmod(row_index - 1, 26)
        label.append(chr(65 + remainder))

    return "".join(reversed(label))

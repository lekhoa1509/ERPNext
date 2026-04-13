import frappe
from frappe import _
from frappe.utils import cint, flt, now_datetime


def build_cell_code(floor, rail, block, depth):
    return f"F{cint(floor)}R{cint(rail)}B{cint(block)}D{cint(depth)}"


def build_cell_label(floor, rail, block, depth):
    return _("Floor {0} - Rail {1} - Block {2} - Depth {3}").format(
        cint(floor),
        cint(rail),
        cint(block),
        cint(depth),
    )


def build_position_code(floor, rail, block):
    return f"F{cint(floor)}R{cint(rail)}B{cint(block)}"


def build_position_label(floor, rail, block):
    return _("Floor {0} - Rail {1} - Block {2}").format(
        cint(floor),
        cint(rail),
        cint(block),
    )


def sync_layout_cells(layout_doc):
    dimensions = get_layout_dimensions(layout_doc)
    if min(dimensions.values()) <= 0:
        return

    existing_cells = {
        (cint(cell.floor), cint(cell.rail), cint(cell.block), cint(cell.depth)): cell
        for cell in frappe.get_all(
            "WH Cell",
            filters={"layout": layout_doc.name},
            fields=["name", "floor", "rail", "block", "depth", "warehouse", "cell_code", "cell_label"],
            limit_page_length=0,
        )
    }

    for floor in range(1, dimensions["total_floors"] + 1):
        for rail in range(1, dimensions["total_rails"] + 1):
            for block in range(1, dimensions["total_blocks"] + 1):
                for depth in range(1, dimensions["total_depths"] + 1):
                    existing = existing_cells.get((floor, rail, block, depth))
                    if existing:
                        updates = {}
                        if layout_doc.warehouse and existing.warehouse != layout_doc.warehouse:
                            updates["warehouse"] = layout_doc.warehouse
                        if not existing.cell_code:
                            updates["cell_code"] = build_cell_code(floor, rail, block, depth)
                        if not existing.cell_label:
                            updates["cell_label"] = build_cell_label(floor, rail, block, depth)
                        if updates:
                            frappe.db.set_value("WH Cell", existing.name, updates, update_modified=False)
                        continue

                    frappe.get_doc(
                        {
                            "doctype": "WH Cell",
                            "layout": layout_doc.name,
                            "warehouse": layout_doc.warehouse,
                            "floor": floor,
                            "rail": rail,
                            "block": block,
                            "depth": depth,
                            "cell_code": build_cell_code(floor, rail, block, depth),
                            "cell_label": build_cell_label(floor, rail, block, depth),
                            "status": "Available",
                        }
                    ).insert(ignore_permissions=True)


def get_layout_overview(layout_name):
    layout_doc = frappe.get_doc("WH Layout", layout_name)
    sync_layout_cells(layout_doc)
    dimensions = get_layout_dimensions(layout_doc)

    cells = frappe.get_all(
        "WH Cell",
        filters={"layout": layout_doc.name},
        fields=[
            "name",
            "cell_code",
            "cell_label",
            "floor",
            "rail",
            "block",
            "depth",
            "status",
            "capacity_qty",
            "notes",
        ],
        order_by="floor asc, rail asc, block asc, depth asc",
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
    position_map = {}
    for cell in cells:
        cell_stock_rows = stock_map.get(cell.name, [])
        total_qty = sum(flt(row["qty"]) for row in cell_stock_rows)
        cell_payload = {
            "name": cell.name,
            "cell_code": cell.cell_code,
            "cell_label": cell.cell_label,
            "floor": cint(cell.floor),
            "rail": cint(cell.rail),
            "block": cint(cell.block),
            "depth": cint(cell.depth),
            "status": cell.status,
            "capacity_qty": flt(cell.capacity_qty),
            "notes": cell.notes,
            "total_qty": total_qty,
            "item_count": len(cell_stock_rows),
            "stock_rows": cell_stock_rows,
        }
        layout_cells.append(cell_payload)

        position_key = (cell_payload["floor"], cell_payload["rail"], cell_payload["block"])
        position = position_map.get(position_key)
        if not position:
            position = {
                "position_code": build_position_code(*position_key),
                "position_label": build_position_label(*position_key),
                "floor": cell_payload["floor"],
                "rail": cell_payload["rail"],
                "block": cell_payload["block"],
                "status": "Available",
                "depth_cells": [],
                "total_qty": 0,
                "item_count": 0,
                "occupied_depths": 0,
            }
            position_map[position_key] = position

        position["status"] = _merge_position_status(position["status"], cell_payload["status"])
        position["total_qty"] += total_qty
        position["item_count"] += len(cell_stock_rows)
        if total_qty > 0:
            position["occupied_depths"] += 1
        position["depth_cells"].append(cell_payload)

    positions = []
    for position_key in sorted(position_map):
        position = position_map[position_key]
        position["depth_cells"] = sorted(position["depth_cells"], key=lambda row: row["depth"])
        positions.append(position)

    return {
        "layout": {
            "name": layout_doc.name,
            "layout_name": layout_doc.layout_name,
            "warehouse": layout_doc.warehouse,
            "company": layout_doc.company,
            **dimensions,
        },
        "cells": layout_cells,
        "positions": positions,
    }


def build_bridge_layout_payload(layout_doc_or_name):
    layout_doc = (
        frappe.get_doc("WH Layout", layout_doc_or_name)
        if isinstance(layout_doc_or_name, str)
        else layout_doc_or_name
    )
    dimensions = get_layout_dimensions(layout_doc)
    disabled_locations = []
    seen_locations = set()

    for cell in frappe.get_all(
        "WH Cell",
        filters={"layout": layout_doc.name, "status": "Blocked"},
        fields=["floor", "rail", "block", "depth"],
        order_by="floor asc, rail asc, block asc, depth asc",
        limit_page_length=0,
    ):
        location = (
            cint(cell.floor),
            cint(cell.rail),
            cint(cell.block),
            cint(cell.depth),
        )
        if location in seen_locations:
            continue

        seen_locations.add(location)
        disabled_locations.append(
            {
                "floor": location[0],
                "rail": location[1],
                "block": location[2],
                "depth": location[3],
            }
        )

    return {
        "blocks": [
            {
                "blockNumber": block_number,
                "maxFloor": dimensions["total_floors"],
                "maxRail": dimensions["total_rails"],
                "maxDepth": dimensions["total_depths"],
            }
            for block_number in range(1, dimensions["total_blocks"] + 1)
        ],
        "disabledLocations": disabled_locations,
    }


def validate_cell_assignment(cell_name, layout=None, warehouse=None):
    if not cell_name:
        return None

    cell = frappe.get_cached_value(
        "WH Cell",
        cell_name,
        ["name", "layout", "warehouse", "status", "cell_code", "floor", "rail", "block", "depth"],
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


def get_layout_dimensions(layout_doc):
    return {
        "total_floors": max(cint(getattr(layout_doc, "total_floors", None) or 1), 0),
        "total_rails": max(
            cint(getattr(layout_doc, "total_rails", None) or getattr(layout_doc, "total_rows", None) or 0),
            0,
        ),
        "total_blocks": max(
            cint(getattr(layout_doc, "total_blocks", None) or getattr(layout_doc, "total_columns", None) or 0),
            0,
        ),
        "total_depths": max(cint(getattr(layout_doc, "total_depths", None) or 1), 0),
    }


def _merge_position_status(current_status, next_status):
    priorities = {
        "Blocked": 3,
        "Reserved": 2,
        "Available": 1,
    }
    current_status = current_status or "Available"
    next_status = next_status or "Available"
    return current_status if priorities.get(current_status, 0) >= priorities.get(next_status, 0) else next_status

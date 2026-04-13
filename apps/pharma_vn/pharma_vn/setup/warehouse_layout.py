import re

import frappe
from frappe.utils import cint

from pharma_vn.warehouse_layout_2d.service import build_cell_code, build_cell_label


LEGACY_CELL_CODE_PATTERN = re.compile(r"^[A-Z]+\d+$")


def migrate_warehouse_layout_to_wcs_coordinates():
    if not frappe.db.table_exists("tabWH Layout") or not frappe.db.table_exists("tabWH Cell"):
        return

    _migrate_layout_dimensions()
    _migrate_cells()


def _migrate_layout_dimensions():
    layout_fields = ["name", "total_floors", "total_rails", "total_blocks", "total_depths"]
    if frappe.db.has_column("WH Layout", "total_rows"):
        layout_fields.append("total_rows")
    if frappe.db.has_column("WH Layout", "total_columns"):
        layout_fields.append("total_columns")

    for layout in frappe.get_all("WH Layout", fields=layout_fields, limit_page_length=0):
        legacy_rows = cint(getattr(layout, "total_rows", 0))
        legacy_columns = cint(getattr(layout, "total_columns", 0))

        total_floors = cint(layout.total_floors) or 1
        total_rails = cint(layout.total_rails) or legacy_rows or 1
        total_blocks = cint(layout.total_blocks) or legacy_columns or 1
        total_depths = cint(layout.total_depths) or 1

        updates = {}
        if cint(layout.total_floors) != total_floors:
            updates["total_floors"] = total_floors
        if cint(layout.total_rails) != total_rails:
            updates["total_rails"] = total_rails
        if cint(layout.total_blocks) != total_blocks:
            updates["total_blocks"] = total_blocks
        if cint(layout.total_depths) != total_depths:
            updates["total_depths"] = total_depths
        if hasattr(layout, "total_rows") and legacy_rows != total_rails:
            updates["total_rows"] = total_rails
        if hasattr(layout, "total_columns") and legacy_columns != total_blocks:
            updates["total_columns"] = total_blocks

        if updates:
            frappe.db.set_value("WH Layout", layout.name, updates, update_modified=False)


def _migrate_cells():
    cell_fields = ["name", "floor", "rail", "block", "depth", "cell_code", "cell_label"]
    if frappe.db.has_column("WH Cell", "row_index"):
        cell_fields.append("row_index")
    if frappe.db.has_column("WH Cell", "column_index"):
        cell_fields.append("column_index")

    for cell in frappe.get_all("WH Cell", fields=cell_fields, limit_page_length=0):
        legacy_row_index = cint(getattr(cell, "row_index", 0))
        legacy_column_index = cint(getattr(cell, "column_index", 0))

        floor = cint(cell.floor) or 1
        rail = cint(cell.rail) or legacy_row_index or 1
        block = cint(cell.block) or legacy_column_index or 1
        depth = cint(cell.depth) or 1

        expected_code = build_cell_code(floor, rail, block, depth)
        expected_label = build_cell_label(floor, rail, block, depth)

        updates = {}
        if cint(cell.floor) != floor:
            updates["floor"] = floor
        if cint(cell.rail) != rail:
            updates["rail"] = rail
        if cint(cell.block) != block:
            updates["block"] = block
        if cint(cell.depth) != depth:
            updates["depth"] = depth
        if hasattr(cell, "row_index") and legacy_row_index != rail:
            updates["row_index"] = rail
        if hasattr(cell, "column_index") and legacy_column_index != block:
            updates["column_index"] = block
        if not cell.cell_code or LEGACY_CELL_CODE_PATTERN.match(cell.cell_code):
            updates["cell_code"] = expected_code
        if not cell.cell_label or str(cell.cell_label).startswith("Row "):
            updates["cell_label"] = expected_label

        if updates:
            frappe.db.set_value("WH Cell", cell.name, updates, update_modified=False)

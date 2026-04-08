import frappe
from frappe import _
from frappe.utils import flt, now_datetime

from pharma_vn.automation.next_documents import create_follow_up_for_delivery_note
from pharma_vn.automation.transaction_taxes import sync_transaction_taxes
from pharma_vn.utils.batch import assert_batch_is_sellable
from pharma_vn.warehouse_layout_2d.service import (
    apply_cell_movement,
    validate_cell_assignment,
    warehouse_has_active_layout,
)


def validate_delivery_note(doc, method=None):
    sync_transaction_taxes(doc, method=method)
    validate_released_batches(doc, method=method)


def _get_row_batch_nos(row):
    batch_nos = []
    child_doctype = row.doctype or "Delivery Note Item"

    batch_no = row.batch_no or frappe.db.get_value(child_doctype, row.name, "batch_no")
    if batch_no:
        batch_nos.append(batch_no)

    bundle = row.serial_and_batch_bundle or frappe.db.get_value(
        child_doctype, row.name, "serial_and_batch_bundle"
    )
    if not bundle:
        return list(dict.fromkeys(batch_nos))

    from erpnext.stock.serial_batch_bundle import get_batch_nos

    for batch_no, details in (get_batch_nos(bundle) or {}).items():
        if details and details.get("qty"):
            batch_nos.append(batch_no)

    return list(dict.fromkeys(batch_nos))


def validate_released_batches(doc, method=None):
    for row in doc.items:
        for batch_no in _get_row_batch_nos(row):
            assert_batch_is_sellable(
                batch_no=batch_no,
                item_code=row.item_code,
                posting_date=doc.posting_date,
            )


def validate_storage_locations_for_submit(doc, method=None):
    for row in doc.items:
        item_code = _row_value(row, "item_code")
        warehouse = _row_value(row, "warehouse")
        wh_layout = _row_value(row, "wh_layout")
        wh_cell = _row_value(row, "wh_cell")

        if not item_code or not warehouse or not _is_stock_item(item_code):
            continue

        if not wh_cell and warehouse_has_active_layout(warehouse):
            frappe.throw(
                _("Row #{0}: warehouse {1} uses Warehouse Layout 2D, please choose a picking cell before submit.").format(
                    row.idx,
                    warehouse,
                )
            )

        if not wh_cell:
            continue

        cell = validate_cell_assignment(
            wh_cell,
            layout=wh_layout or None,
            warehouse=warehouse,
        )
        if not wh_layout:
            row.wh_layout = cell.layout

        _ensure_cell_has_stock(
            row=row,
            cell_name=wh_cell,
            warehouse=warehouse,
        )


def handle_delivery_note_on_submit(doc, method=None):
    _sync_storage_locations(doc, is_reversal=False)
    create_follow_up_for_delivery_note(doc, method=method)


def handle_delivery_note_on_cancel(doc, method=None):
    _sync_storage_locations(doc, is_reversal=True)


def _sync_storage_locations(doc, is_reversal=False):
    posting_datetime_value = now_datetime()
    if doc.get("posting_date") and doc.get("posting_time"):
        posting_datetime_value = f"{doc.posting_date} {doc.posting_time}"
    elif doc.get("posting_date"):
        posting_datetime_value = f"{doc.posting_date} 00:00:00"

    for row in doc.items:
        wh_cell = row.get("wh_cell")
        wh_layout = row.get("wh_layout")
        movement_qty = flt(row.stock_qty or row.qty)
        if not movement_qty or not row.item_code or not wh_cell:
            continue

        cell = validate_cell_assignment(
            wh_cell,
            layout=wh_layout or None,
            warehouse=row.warehouse,
        )

        qty_delta = movement_qty if is_reversal else -movement_qty
        movement_type = "Adjustment" if is_reversal else "Outbound"

        apply_cell_movement(
            cell_name=wh_cell,
            layout_name=cell.layout,
            warehouse=row.warehouse,
            item_code=row.item_code,
            batch_no=_resolve_row_batch_no(row),
            qty_delta=qty_delta,
            uom=row.stock_uom or row.uom,
            movement_type=movement_type,
            posting_datetime_value=posting_datetime_value,
            source_doctype=doc.doctype,
            source_name=doc.name,
            source_row_name=row.name,
            remarks=_build_movement_remark(doc.name, row.idx, is_reversal=is_reversal),
        )


def _ensure_cell_has_stock(*, row, cell_name, warehouse):
    filters = {
        "cell": cell_name,
        "warehouse": warehouse,
        "item_code": row.item_code,
    }
    batch_no = _resolve_row_batch_no(row)
    if batch_no:
        filters["batch_no"] = batch_no

    stock_rows = frappe.get_all(
        "WH Cell Stock",
        filters=filters,
        fields=["qty"],
        limit_page_length=0,
    )
    available_qty = sum(flt(stock_row.qty) for stock_row in stock_rows)
    required_qty = flt(row.stock_qty or row.qty)

    if available_qty + 0.0001 < required_qty:
        frappe.throw(
            _("Row #{0}: cell {1} only has {2} available for item {3}, but the document needs {4}.").format(
                row.idx,
                cell_name,
                available_qty,
                row.item_code,
                required_qty,
            )
        )


def _resolve_row_batch_no(row):
    batch_nos = _get_row_batch_nos(row)
    return batch_nos[0] if batch_nos else None


def _is_stock_item(item_code):
    if not frappe.db.exists("Item", item_code):
        return False

    return bool(frappe.get_cached_value("Item", item_code, "is_stock_item"))


def _row_value(row, fieldname, default=None):
    getter = getattr(row, "get", None)
    if callable(getter):
        value = getter(fieldname)
        return default if value is None else value

    return getattr(row, fieldname, default)


def _build_movement_remark(delivery_note, row_idx, is_reversal=False):
    if is_reversal:
        return f"Reversed from Delivery Note {delivery_note}, row {row_idx}."

    return f"Outbound from Delivery Note {delivery_note}, row {row_idx}."

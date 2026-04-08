import frappe
from frappe import _
from frappe.utils import flt, now_datetime

from pharma_vn.automation.next_documents import create_follow_up_for_purchase_receipt
from pharma_vn.automation.transaction_taxes import sync_transaction_taxes
from pharma_vn.warehouse_layout_2d.service import (
    apply_cell_movement,
    validate_cell_assignment,
    warehouse_has_active_layout,
)


def validate_purchase_receipt(doc, method=None):
    sync_transaction_taxes(doc, method=method)
    validate_storage_locations(doc, method=method)


def create_pending_batch_releases(doc, method=None):
    for row in doc.items:
        batch_no = _get_row_batch_no(row)
        if not batch_no or not _item_requires_qa(row.item_code):
            continue

        if frappe.db.exists(
            "PH Batch Release",
            {
                "batch_no": batch_no,
                "source_doctype": doc.doctype,
                "source_name": doc.name,
            },
        ):
            continue

        pending_release = frappe.get_doc(
            {
                "doctype": "PH Batch Release",
                "batch_no": batch_no,
                "item_code": row.item_code,
                "warehouse": row.warehouse,
                "source_doctype": doc.doctype,
                "source_name": doc.name,
                "status": "Draft",
                "release_date": now_datetime(),
                "remarks": "Auto-created from Purchase Receipt for QA review.",
            }
        )
        pending_release.insert(ignore_permissions=True)
        frappe.db.set_value("Batch", batch_no, "batch_status", "QA", update_modified=False)


def validate_storage_locations(doc, method=None):
    if getattr(doc.flags, "pharma_skip_storage_validation", False):
        return

    for row in doc.items:
        item_code = _row_value(row, "item_code")
        warehouse = _row_value(row, "warehouse")
        wh_layout = _row_value(row, "wh_layout")
        wh_cell = _row_value(row, "wh_cell")

        if not item_code or not warehouse:
            continue

        if not _is_stock_item(item_code):
            continue

        if wh_layout and not wh_cell:
            frappe.throw(
                _("Row #{0}: please choose a WH Cell for layout {1}.").format(row.idx, wh_layout)
            )

        if not wh_cell:
            if warehouse_has_active_layout(warehouse):
                frappe.throw(
                    _("Row #{0}: warehouse {1} uses Warehouse Layout 2D, please choose a storage cell.").format(
                        row.idx,
                        warehouse,
                    )
                )
            continue

        cell = validate_cell_assignment(
            wh_cell,
            layout=wh_layout or None,
            warehouse=warehouse,
        )
        if not wh_layout:
            row.wh_layout = cell.layout


def handle_purchase_receipt_on_submit(doc, method=None):
    create_pending_batch_releases(doc, method=method)
    _sync_storage_locations(doc, is_reversal=False)
    create_follow_up_for_purchase_receipt(doc, method=method)


def handle_purchase_receipt_on_cancel(doc, method=None):
    _sync_storage_locations(doc, is_reversal=True)


def _get_row_batch_no(row):
    child_doctype = row.doctype or "Purchase Receipt Item"
    batch_no = row.batch_no or frappe.db.get_value(child_doctype, row.name, "batch_no")
    if batch_no:
        return batch_no

    bundle = row.serial_and_batch_bundle or frappe.db.get_value(
        child_doctype, row.name, "serial_and_batch_bundle"
    )
    if not bundle:
        return None

    from erpnext.stock.serial_batch_bundle import get_batch_nos

    batches = get_batch_nos(bundle) or {}
    return next(iter(batches.keys()), None)


def _item_requires_qa(item_code):
    if not frappe.db.exists("Item", item_code):
        return False

    if frappe.db.has_column("Item", "qa_required"):
        return bool(frappe.db.get_value("Item", item_code, "qa_required"))

    return True


def _is_stock_item(item_code):
    if not frappe.db.exists("Item", item_code):
        return False

    return bool(frappe.get_cached_value("Item", item_code, "is_stock_item"))


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
        qty_delta = -movement_qty if is_reversal else movement_qty
        movement_type = "Adjustment" if is_reversal else "Inbound"

        apply_cell_movement(
            cell_name=wh_cell,
            layout_name=cell.layout,
            warehouse=row.warehouse,
            item_code=row.item_code,
            batch_no=_get_row_batch_no(row),
            qty_delta=qty_delta,
            uom=row.stock_uom or row.uom,
            movement_type=movement_type,
            posting_datetime_value=posting_datetime_value,
            source_doctype=doc.doctype,
            source_name=doc.name,
            source_row_name=row.name,
            remarks=_build_movement_remark(doc.name, row.idx, is_reversal=is_reversal),
        )


def _build_movement_remark(purchase_receipt, row_idx, is_reversal=False):
    if is_reversal:
        return f"Reversed from Purchase Receipt {purchase_receipt}, row {row_idx}."

    return f"Inbound from Purchase Receipt {purchase_receipt}, row {row_idx}."


def _row_value(row, fieldname, default=None):
    getter = getattr(row, "get", None)
    if callable(getter):
        value = getter(fieldname)
        return default if value is None else value

    return getattr(row, fieldname, default)

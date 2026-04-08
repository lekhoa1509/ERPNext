import frappe
from frappe import _
from frappe.utils import getdate, nowdate

from pharma_vn.utils.response import ok


def _is_batch_sellable(batch_no, posting_date, item_code):
    batch_fields = frappe.get_cached_value(
        "Batch",
        batch_no,
        ["expiry_date", "batch_status", "temperature_excursion_flag"],
        as_dict=True,
    )
    if not batch_fields:
        return False

    if batch_fields.batch_status != "Released":
        return False

    if batch_fields.temperature_excursion_flag:
        return False

    expiry_date = batch_fields.expiry_date
    if expiry_date and getdate(expiry_date) < getdate(posting_date):
        return False

    min_remaining_days = frappe.get_cached_value("Item", item_code, "min_remaining_shelf_life_days") or 0
    if expiry_date and min_remaining_days:
        remaining_days = (getdate(expiry_date) - getdate(posting_date)).days
        if remaining_days < int(min_remaining_days):
            return False

    return True


@frappe.whitelist()
def get_sellable_stock(item_code=None, warehouse=None, company=None, posting_date=None, posting_time=None):
    item_code = item_code or frappe.form_dict.get("item_code")
    warehouse = warehouse or frappe.form_dict.get("warehouse")
    company = company or frappe.form_dict.get("company")
    posting_date = posting_date or frappe.form_dict.get("posting_date") or nowdate()
    posting_time = posting_time or frappe.form_dict.get("posting_time") or "00:00:00"

    if not item_code:
        frappe.throw(_("item_code is required"))

    from erpnext.stock.doctype.serial_and_batch_bundle.serial_and_batch_bundle import get_available_batches

    rows = get_available_batches(
        frappe._dict(
            {
                "item_code": item_code,
                "warehouse": warehouse,
                "company": company,
                "posting_date": posting_date,
                "posting_time": posting_time,
                "based_on": "Expiry",
            }
        )
    )

    sellable_rows = []
    for row in rows or []:
        if not row.get("batch_no") or not row.get("qty"):
            continue

        if not _is_batch_sellable(row.batch_no, posting_date, item_code):
            continue

        sellable_rows.append(
            {
                "item_code": item_code,
                "warehouse": row.warehouse,
                "batch_no": row.batch_no,
                "qty": row.qty,
                "expiry_date": row.expiry_date,
            }
        )

    sellable_rows.sort(
        key=lambda d: (
            d.get("expiry_date") or "9999-12-31",
            d.get("warehouse") or "",
            d.get("batch_no") or "",
        )
    )

    return ok(_("Sellable stock fetched"), {"item_code": item_code, "rows": sellable_rows})

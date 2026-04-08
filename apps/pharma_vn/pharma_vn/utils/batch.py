import frappe
from frappe import _
from frappe.utils import cint, date_diff, getdate, nowdate


SELLABLE_BATCH_STATUSES = {"", None, "Released", "Approved"}


def assert_batch_is_sellable(batch_no, item_code=None, posting_date=None):
    if not frappe.db.exists("Batch", batch_no):
        frappe.throw(_("Batch {0} does not exist").format(batch_no))

    batch_status = get_batch_status(batch_no)
    if batch_status not in SELLABLE_BATCH_STATUSES:
        frappe.throw(_("Batch {0} is not released for sale").format(batch_no))

    if _has_batch_flag("temperature_excursion_flag"):
        excursion_flag = frappe.db.get_value("Batch", batch_no, "temperature_excursion_flag")
        if excursion_flag:
            frappe.throw(_("Batch {0} is on hold due to temperature excursion").format(batch_no))

    assert_minimum_remaining_shelf_life(
        batch_no=batch_no, item_code=item_code, posting_date=posting_date
    )


def assert_minimum_remaining_shelf_life(batch_no, item_code=None, posting_date=None):
    item_code = item_code or frappe.db.get_value("Batch", batch_no, "item")
    expiry_date = frappe.db.get_value("Batch", batch_no, "expiry_date")

    if not expiry_date or not item_code:
        return

    posting_date = getdate(posting_date or nowdate())
    min_days = _get_minimum_remaining_shelf_life_days(item_code)
    remaining_days = date_diff(getdate(expiry_date), posting_date)

    if min_days and remaining_days < min_days:
        frappe.throw(
            _(
                "Batch {0} has only {1} day(s) remaining, below the minimum shelf life {2}."
            ).format(batch_no, remaining_days, min_days)
        )


def get_batch_status(batch_no):
    if not _has_batch_flag("batch_status"):
        return "Released"

    return frappe.db.get_value("Batch", batch_no, "batch_status")


def update_batch_fields(batch_no, values):
    meta = frappe.get_meta("Batch")
    allowed_values = {key: value for key, value in values.items() if meta.has_field(key)}

    if allowed_values:
        frappe.db.set_value("Batch", batch_no, allowed_values, update_modified=True)


def _get_minimum_remaining_shelf_life_days(item_code):
    default_value = cint(frappe.db.get_default("pharma_default_shelf_life_days") or 0)
    if not frappe.db.exists("Item", item_code):
        return default_value

    if frappe.db.has_column("Item", "min_remaining_shelf_life_days"):
        return cint(
            frappe.db.get_value("Item", item_code, "min_remaining_shelf_life_days")
            or default_value
        )

    return default_value


def _has_batch_flag(fieldname):
    return frappe.db.has_column("Batch", fieldname)


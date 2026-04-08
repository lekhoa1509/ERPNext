import frappe


TRANSACTION_DOCTYPES = [
    "Payment Entry",
    "Sales Invoice",
    "Purchase Invoice",
    "Delivery Note",
    "Purchase Receipt",
    "Sales Order",
    "Purchase Order",
    "Quotation",
    "Supplier Quotation",
    "Request for Quotation",
    "Material Request",
    "Stock Entry",
]

LEDGER_DOCTYPES = [
    "Payment Ledger Entry",
    "GL Entry",
    "Stock Ledger Entry",
    "Serial and Batch Bundle",
    "Bin",
]

RESET_SERIES = [
    "ACC-PAY-.YYYY.-",
    "ACC-PINV-.YYYY.-",
    "ACC-SINV-.YYYY.-",
    "MAT-DN-.YYYY.-",
    "MAT-STE-.YYYY.-",
    "PUR-ORD-.YYYY.-",
    "PUR-REC-.YYYY.-",
    "PUR-RFQ-.YYYY.-",
    "QTN-.YYYY.-",
    "SAL-ORD-.YYYY.-",
]

BOOTSTRAP_ITEM_GROUPS = [
    "OTC Products",
    "ETC Products",
    "Supplements",
]


def prepare_import_site():
    summary = {
        "cancelled": {},
        "deleted_docs": {},
        "deleted_rows": {},
        "reset_series": [],
    }

    try:
        _delete_transactions(summary)
        _delete_rows(summary, "PH Batch Release")
        _delete_rows(summary, "WH Cell Movement")
        _delete_rows(summary, "WH Cell Stock")
        _delete_rows(summary, "WH Cell")
        _delete_rows(summary, "WH Layout")
        _delete_rows(summary, "Batch")
        _delete_master_contacts(summary)
        _delete_master_docs(summary, "Customer")
        _delete_master_docs(summary, "Supplier")
        _delete_master_docs(summary, "Item Price")
        _delete_master_docs(summary, "Item")
        _delete_bootstrap_item_groups(summary)
        _delete_rows(summary, "Dynamic Link", {"link_doctype": ["in", ["Customer", "Supplier"]]})
        _delete_ledgers(summary)
        _reset_series(summary)
        frappe.db.commit()
    except Exception:
        frappe.db.rollback()
        raise

    frappe.clear_cache()
    return summary


def _delete_transactions(summary):
    for doctype in TRANSACTION_DOCTYPES:
        names = frappe.get_all(doctype, pluck="name", order_by="creation desc")
        deleted = 0

        for name in names:
            _hard_delete_doc_rows(doctype, name)
            deleted += 1

        if deleted:
            summary["deleted_docs"][doctype] = deleted


def _hard_delete_doc_rows(doctype, name):
    meta = frappe.get_meta(doctype)
    for df in meta.fields:
        if df.fieldtype not in ("Table", "Table MultiSelect") or not df.options:
            continue

        if not frappe.db.table_exists(df.options):
            continue

        frappe.db.delete(
            df.options,
            {
                "parent": name,
                "parenttype": doctype,
                "parentfield": df.fieldname,
            },
        )

    frappe.db.delete(doctype, {"name": name})


def _delete_master_contacts(summary):
    address_names = _linked_master_names("Address")
    contact_names = _linked_master_names("Contact")

    deleted_addresses = 0
    for name in address_names:
        frappe.delete_doc("Address", name, ignore_permissions=True, force=True)
        deleted_addresses += 1
    if deleted_addresses:
        summary["deleted_docs"]["Address"] = deleted_addresses

    deleted_contacts = 0
    for name in contact_names:
        frappe.delete_doc("Contact", name, ignore_permissions=True, force=True)
        deleted_contacts += 1
    if deleted_contacts:
        summary["deleted_docs"]["Contact"] = deleted_contacts


def _linked_master_names(parenttype):
    return list(
        {
            row.parent
            for row in frappe.get_all(
                "Dynamic Link",
                filters={
                    "parenttype": parenttype,
                    "link_doctype": ["in", ["Customer", "Supplier"]],
                },
                fields=["parent"],
            )
            if row.parent
        }
    )


def _delete_master_docs(summary, doctype):
    if not _doctype_available(doctype):
        return

    deleted = 0
    for name in frappe.get_all(doctype, pluck="name", order_by="creation desc"):
        frappe.delete_doc(doctype, name, ignore_permissions=True, force=True)
        deleted += 1
    if deleted:
        summary["deleted_docs"][doctype] = deleted


def _delete_bootstrap_item_groups(summary):
    if not _doctype_available("Item Group"):
        return

    deleted = 0
    for name in BOOTSTRAP_ITEM_GROUPS:
        if not frappe.db.exists("Item Group", name):
            continue
        frappe.delete_doc("Item Group", name, ignore_permissions=True, force=True)
        deleted += 1
    if deleted:
        summary["deleted_docs"]["Item Group"] = deleted


def _delete_ledgers(summary):
    for doctype in LEDGER_DOCTYPES:
        _delete_rows(summary, doctype)


def _delete_rows(summary, doctype, filters=None):
    if not _doctype_available(doctype):
        return

    count = frappe.db.count(doctype, filters=filters)
    if not count:
        return
    frappe.db.delete(doctype, filters or {})
    summary["deleted_rows"][doctype] = count


def _reset_series(summary):
    for series_name in RESET_SERIES:
        if not frappe.db.exists("Series", series_name):
            continue
        frappe.db.set_value("Series", series_name, "current", 0, update_modified=False)
        summary["reset_series"].append(series_name)


def _doctype_available(doctype):
    return bool(frappe.db.exists("DocType", doctype))

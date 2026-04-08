import frappe


def create_follow_up_for_purchase_order(doc, method=None):
    return _ensure_follow_up_document(
        source_doc=doc,
        source_doctype="Purchase Order",
        target_doctype="Purchase Receipt",
        mapper_path="erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_receipt",
        child_doctype="Purchase Receipt Item",
        link_field="purchase_order",
    )


def create_follow_up_for_purchase_receipt(doc, method=None):
    return _ensure_follow_up_document(
        source_doc=doc,
        source_doctype="Purchase Receipt",
        target_doctype="Purchase Invoice",
        mapper_path="erpnext.stock.doctype.purchase_receipt.purchase_receipt.make_purchase_invoice",
        child_doctype="Purchase Invoice Item",
        link_field="purchase_receipt",
    )


def create_follow_up_for_sales_order(doc, method=None):
    return _ensure_follow_up_document(
        source_doc=doc,
        source_doctype="Sales Order",
        target_doctype="Delivery Note",
        mapper_path="erpnext.selling.doctype.sales_order.sales_order.make_delivery_note",
        child_doctype="Delivery Note Item",
        link_field="against_sales_order",
    )


def create_follow_up_for_delivery_note(doc, method=None):
    return _ensure_follow_up_document(
        source_doc=doc,
        source_doctype="Delivery Note",
        target_doctype="Sales Invoice",
        mapper_path="erpnext.stock.doctype.delivery_note.delivery_note.make_sales_invoice",
        child_doctype="Sales Invoice Item",
        link_field="delivery_note",
    )


def _ensure_follow_up_document(*, source_doc, source_doctype, target_doctype, mapper_path, child_doctype, link_field):
    if source_doc.doctype != source_doctype or source_doc.docstatus != 1:
        return None

    existing_draft = _find_existing_draft(target_doctype, child_doctype, link_field, source_doc.name)
    if existing_draft:
        _notify_existing_draft(source_doc.name, target_doctype, existing_draft)
        return existing_draft

    mapper = frappe.get_attr(mapper_path)
    try:
        target_doc = mapper(source_doc.name)
    except Exception:
        frappe.log_error(
            title=f"Auto create {target_doctype} draft failed",
            message=frappe.get_traceback(),
        )
        return None

    if not target_doc:
        return None
    if not getattr(target_doc, "items", None):
        return None

    target_doc.flags.pharma_skip_storage_validation = True
    target_doc.flags.ignore_permissions = True
    target_doc.insert(ignore_permissions=True)
    _notify_created_draft(source_doc.name, target_doctype, target_doc.name)
    return target_doc.name


def _find_existing_draft(target_doctype, child_doctype, link_field, source_name):
    rows = frappe.get_all(
        child_doctype,
        filters={link_field: source_name},
        fields=["parent"],
        limit_page_length=20,
    )
    for row in rows:
        if frappe.db.get_value(target_doctype, row["parent"], "docstatus") == 0:
            return row["parent"]
    return None


def _notify_created_draft(source_name, target_doctype, target_name):
    frappe.msgprint(
        f"Da tu dong tao nhap {target_doctype} draft {target_name} tu chung tu {source_name}.",
        alert=True,
        indicator="green",
    )


def _notify_existing_draft(source_name, target_doctype, target_name):
    frappe.msgprint(
        f"Da co {target_doctype} draft {target_name} duoc tao truoc do cho chung tu {source_name}.",
        alert=True,
        indicator="blue",
    )

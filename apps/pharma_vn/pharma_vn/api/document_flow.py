import frappe
from frappe import _


SUPPORTED_DOCTYPES = {
    "Quotation",
    "Sales Order",
    "Delivery Note",
    "Sales Invoice",
    "Material Request",
    "Purchase Order",
    "Purchase Receipt",
    "Purchase Invoice",
    "Payment Entry",
    "Stock Entry",
}

SALES_FLOW_STEPS = [
    {"key": "quotation", "title": "Quotation", "description": "Báo giá và điều khoản thương mại"},
    {"key": "sales_order", "title": "Sales Order", "description": "Xác nhận đơn hàng bán"},
    {"key": "outbound_delivery", "title": "Delivery Note", "description": "Xuất kho và giao hàng"},
    {"key": "customer_invoice", "title": "Sales Invoice", "description": "Lập hóa đơn bán hàng"},
    {"key": "incoming_payment", "title": "Payment Entry", "description": "Thu tiền khách hàng"},
]

PURCHASE_FLOW_STEPS = [
    {"key": "material_request", "title": "Material Request", "description": "Nhu cầu mua hoặc cấp hàng"},
    {"key": "purchase_order", "title": "Purchase Order", "description": "Đơn mua gửi nhà cung cấp"},
    {"key": "purchase_receipt", "title": "Purchase Receipt", "description": "Nhập kho hàng mua"},
    {"key": "purchase_invoice", "title": "Purchase Invoice", "description": "Hóa đơn mua hàng"},
    {"key": "outgoing_payment", "title": "Payment Entry", "description": "Thanh toán nhà cung cấp"},
]


@frappe.whitelist()
def get_document_flow(doctype=None, name=None):
    doctype = doctype or frappe.form_dict.get("doctype")
    name = name or frappe.form_dict.get("name")

    if not doctype or not name:
        frappe.throw(_("doctype and name are required"))

    if doctype not in SUPPORTED_DOCTYPES:
        frappe.throw(_("Document Flow is not configured for this document type"))

    context = _resolve_flow_context(doctype, name)
    if not context:
        return {
            "ok": False,
            "doctype": doctype,
            "name": name,
            "message": "Chưa dựng được document flow cho chứng từ này.",
        }

    if context["flow_type"] == "sales":
        return _build_sales_flow(context, doctype, name)

    if context["flow_type"] == "purchase":
        return _build_purchase_flow(context, doctype, name)

    if context["flow_type"] == "stock":
        return _build_stock_entry_flow(context, doctype, name)

    return {
        "ok": False,
        "doctype": doctype,
        "name": name,
        "message": "Chưa có cấu hình document flow cho chứng từ này.",
    }


def _resolve_flow_context(doctype, name):
    if doctype in {"Quotation", "Sales Order", "Delivery Note", "Sales Invoice"}:
        return _resolve_sales_context(doctype, name)

    if doctype in {"Material Request", "Purchase Order", "Purchase Receipt", "Purchase Invoice"}:
        return _resolve_purchase_context(doctype, name)

    if doctype == "Payment Entry":
        return _resolve_payment_entry_context(name)

    if doctype == "Stock Entry":
        return {"flow_type": "stock", "stock_entry": name}

    return None


def _resolve_sales_context(doctype, name):
    quotation_name = None
    sales_order_name = None

    if doctype == "Quotation":
        quotation_name = name
        sales_order_name = _first_value(
            "Sales Order Item",
            filters={"prevdoc_docname": quotation_name},
            fieldname="parent",
        )
    elif doctype == "Sales Order":
        sales_order_name = name
        quotation_name = _first_value(
            "Sales Order Item",
            filters={"parent": name},
            fieldname="prevdoc_docname",
        )
    elif doctype == "Delivery Note":
        sales_order_name = _first_value(
            "Delivery Note Item",
            filters={"parent": name},
            fieldname="against_sales_order",
        )
    elif doctype == "Sales Invoice":
        sales_order_name = _first_value(
            "Sales Invoice Item",
            filters={"parent": name},
            fieldname="sales_order",
        )
        if not sales_order_name:
            delivery_note = _first_value(
                "Sales Invoice Item",
                filters={"parent": name},
                fieldname="delivery_note",
            )
            if delivery_note:
                sales_order_name = _first_value(
                    "Delivery Note Item",
                    filters={"parent": delivery_note},
                    fieldname="against_sales_order",
                )

    if sales_order_name and not quotation_name:
        quotation_name = _first_value(
            "Sales Order Item",
            filters={"parent": sales_order_name},
            fieldname="prevdoc_docname",
        )

    if quotation_name or sales_order_name:
        return {
            "flow_type": "sales",
            "quotation": quotation_name,
            "sales_order": sales_order_name,
        }

    return None


def _resolve_purchase_context(doctype, name):
    material_request_name = None
    purchase_order_name = None

    if doctype == "Material Request":
        material_request_name = name
        purchase_order_name = _first_value(
            "Purchase Order Item",
            filters={"material_request": name},
            fieldname="parent",
        )
    elif doctype == "Purchase Order":
        purchase_order_name = name
        material_request_name = _first_value(
            "Purchase Order Item",
            filters={"parent": name},
            fieldname="material_request",
        )
    elif doctype == "Purchase Receipt":
        purchase_order_name = _first_value(
            "Purchase Receipt Item",
            filters={"parent": name},
            fieldname="purchase_order",
        )
    elif doctype == "Purchase Invoice":
        purchase_order_name = _first_value(
            "Purchase Invoice Item",
            filters={"parent": name},
            fieldname="purchase_order",
        )
        if not purchase_order_name:
            purchase_receipt = _first_value(
                "Purchase Invoice Item",
                filters={"parent": name},
                fieldname="purchase_receipt",
            )
            if purchase_receipt:
                purchase_order_name = _first_value(
                    "Purchase Receipt Item",
                    filters={"parent": purchase_receipt},
                    fieldname="purchase_order",
                )

    if purchase_order_name and not material_request_name:
        material_request_name = _first_value(
            "Purchase Order Item",
            filters={"parent": purchase_order_name},
            fieldname="material_request",
        )

    if material_request_name or purchase_order_name:
        return {
            "flow_type": "purchase",
            "material_request": material_request_name,
            "purchase_order": purchase_order_name,
        }

    return None


def _resolve_payment_entry_context(name):
    references = frappe.get_all(
        "Payment Entry Reference",
        filters={"parent": name},
        fields=["reference_doctype", "reference_name"],
        limit_page_length=20,
    )

    for row in references:
        ref_doctype = row.get("reference_doctype")
        ref_name = row.get("reference_name")
        if ref_doctype in {"Quotation", "Sales Order", "Delivery Note", "Sales Invoice"}:
            return _resolve_sales_context(ref_doctype, ref_name)
        if ref_doctype in {"Material Request", "Purchase Order", "Purchase Receipt", "Purchase Invoice"}:
            return _resolve_purchase_context(ref_doctype, ref_name)

    return None


def _build_sales_flow(context, anchor_doctype, anchor_name):
    quotation = _get_doc_row(
        "Quotation",
        context.get("quotation"),
        ["name", "status", "docstatus", "transaction_date", "party_name", "quotation_to"],
    )
    sales_order = _get_doc_row(
        "Sales Order",
        context.get("sales_order"),
        [
            "name",
            "status",
            "docstatus",
            "transaction_date",
            "customer",
            "workflow_state",
            "delivery_status",
            "billing_status",
            "per_delivered",
            "per_billed",
        ],
    )

    delivery_notes = _get_sales_delivery_notes(context.get("sales_order"))
    sales_invoices = _get_sales_invoices(context.get("sales_order"), delivery_notes)
    payment_entries = _get_sales_payment_entries(context.get("sales_order"), sales_invoices)

    steps = _init_steps(SALES_FLOW_STEPS)
    steps["quotation"]["documents"] = _serialize_single_doc(
        quotation,
        "Quotation",
        anchor_doctype,
        anchor_name,
        meta_getter=lambda row: row.get("quotation_to"),
    )
    steps["quotation"]["summary"] = _get_sales_quotation_summary(quotation, sales_order)
    steps["sales_order"]["documents"] = _serialize_single_doc(
        sales_order,
        "Sales Order",
        anchor_doctype,
        anchor_name,
        meta_getter=lambda row: row.get("workflow_state") or row.get("status"),
    )
    steps["sales_order"]["summary"] = _get_sales_order_summary(sales_order)
    steps["outbound_delivery"]["documents"] = _serialize_docs(
        delivery_notes,
        "Delivery Note",
        anchor_doctype,
        anchor_name,
        meta_getter=lambda row: row.get("status"),
    )
    steps["customer_invoice"]["documents"] = _serialize_docs(
        sales_invoices,
        "Sales Invoice",
        anchor_doctype,
        anchor_name,
        meta_getter=_format_currency_hint,
    )
    steps["incoming_payment"]["documents"] = _serialize_docs(
        payment_entries,
        "Payment Entry",
        anchor_doctype,
        anchor_name,
        meta_getter=lambda row: row.get("party"),
        status_getter=_get_payment_status,
    )

    current_key = None
    next_step = None
    flow_status = "active"
    flow_message = None

    if not quotation and not sales_order:
        return {
            "ok": False,
            "doctype": anchor_doctype,
            "name": anchor_name,
            "message": "Không tìm thấy chứng từ bán hàng gốc để dựng flow.",
        }

    if not sales_order:
        current_key = "quotation"
        steps["quotation"]["status"] = "current"
        next_step = {"title": "Create Sales Order", "detail": "Tạo Sales Order từ báo giá để chốt đơn."}
    else:
        steps["quotation"]["status"] = "complete" if quotation else "upcoming"
        steps["sales_order"]["status"] = "complete" if sales_order.get("docstatus") == 1 else "current"
        if sales_order.get("docstatus") != 1:
            current_key = "sales_order"
            next_step = {"title": "Submit Sales Order", "detail": "Submit đơn bán để chuyển sang giao hàng."}
        else:
            steps["sales_order"]["status"] = "complete"
            delivery_state = _get_sales_delivery_state(delivery_notes, sales_order)
            invoice_state = _get_sales_invoice_state(sales_invoices, sales_order)
            payment_state = _get_sales_payment_state(payment_entries, sales_invoices)

            steps["outbound_delivery"]["summary"] = delivery_state["summary"]
            steps["customer_invoice"]["summary"] = invoice_state["summary"]
            steps["incoming_payment"]["summary"] = payment_state["summary"]

            if not delivery_state["complete"]:
                current_key = "outbound_delivery"
                steps["outbound_delivery"]["status"] = "current"
                next_step = delivery_state["next_step"]
            elif not invoice_state["complete"]:
                steps["outbound_delivery"]["status"] = "complete"
                current_key = "customer_invoice"
                steps["customer_invoice"]["status"] = "current"
                next_step = invoice_state["next_step"]
            elif not payment_state["complete"]:
                steps["outbound_delivery"]["status"] = "complete"
                steps["customer_invoice"]["status"] = "complete"
                current_key = "incoming_payment"
                steps["incoming_payment"]["status"] = "current"
                next_step = payment_state["next_step"]
            else:
                for step in SALES_FLOW_STEPS:
                    steps[step["key"]]["status"] = "complete"
                current_key = "incoming_payment"
                flow_status = "complete"
                flow_message = "Luồng bán hàng đã hoàn tất."

    _fill_remaining_statuses(steps, SALES_FLOW_STEPS)

    return _build_response(
        flow_type="sales",
        anchor_doctype=anchor_doctype,
        anchor_name=anchor_name,
        steps=steps,
        step_order=SALES_FLOW_STEPS,
        current_key=current_key,
        next_step=next_step,
        flow_status=flow_status,
        flow_message=flow_message,
        overview={
            "company_flow": "Sales",
            "party": sales_order.get("customer") if sales_order else quotation.get("party_name") if quotation else None,
            "delivery_status": sales_order.get("delivery_status") if sales_order else None,
            "invoice_status": sales_order.get("billing_status") if sales_order else None,
        },
    )


def _build_purchase_flow(context, anchor_doctype, anchor_name):
    material_request = _get_doc_row(
        "Material Request",
        context.get("material_request"),
        ["name", "status", "docstatus", "transaction_date", "material_request_type"],
    )
    purchase_order = _get_doc_row(
        "Purchase Order",
        context.get("purchase_order"),
        ["name", "status", "docstatus", "transaction_date", "supplier", "per_received", "per_billed"],
    )

    purchase_receipts = _get_purchase_receipts(context.get("purchase_order"))
    purchase_invoices = _get_purchase_invoices(context.get("purchase_order"), purchase_receipts)
    payment_entries = _get_purchase_payment_entries(context.get("purchase_order"), purchase_invoices)

    steps = _init_steps(PURCHASE_FLOW_STEPS)
    steps["material_request"]["documents"] = _serialize_single_doc(
        material_request,
        "Material Request",
        anchor_doctype,
        anchor_name,
        meta_getter=lambda row: row.get("material_request_type"),
    )
    steps["material_request"]["summary"] = _get_material_request_summary(material_request, purchase_order)
    steps["purchase_order"]["documents"] = _serialize_single_doc(
        purchase_order,
        "Purchase Order",
        anchor_doctype,
        anchor_name,
        meta_getter=lambda row: row.get("status"),
    )
    steps["purchase_order"]["summary"] = _get_purchase_order_summary(purchase_order)
    steps["purchase_receipt"]["documents"] = _serialize_docs(
        purchase_receipts,
        "Purchase Receipt",
        anchor_doctype,
        anchor_name,
        meta_getter=lambda row: row.get("status"),
    )
    steps["purchase_invoice"]["documents"] = _serialize_docs(
        purchase_invoices,
        "Purchase Invoice",
        anchor_doctype,
        anchor_name,
        meta_getter=_format_currency_hint,
    )
    steps["outgoing_payment"]["documents"] = _serialize_docs(
        payment_entries,
        "Payment Entry",
        anchor_doctype,
        anchor_name,
        meta_getter=lambda row: row.get("party"),
        status_getter=_get_payment_status,
    )

    current_key = None
    next_step = None
    flow_status = "active"
    flow_message = None

    if not material_request and not purchase_order:
        return {
            "ok": False,
            "doctype": anchor_doctype,
            "name": anchor_name,
            "message": "Không tìm thấy chứng từ mua hàng gốc để dựng flow.",
        }

    if not purchase_order:
        current_key = "material_request"
        steps["material_request"]["status"] = "current"
        next_step = {"title": "Create Purchase Order", "detail": "Tạo Purchase Order từ Material Request."}
    else:
        steps["material_request"]["status"] = "complete" if material_request else "upcoming"
        steps["purchase_order"]["status"] = "complete" if purchase_order.get("docstatus") == 1 else "current"
        if purchase_order.get("docstatus") != 1:
            current_key = "purchase_order"
            next_step = {"title": "Submit Purchase Order", "detail": "Submit PO để bắt đầu quy trình nhận hàng."}
        else:
            steps["purchase_order"]["status"] = "complete"
            receipt_state = _get_purchase_receipt_state(purchase_receipts, purchase_order)
            invoice_state = _get_purchase_invoice_state(purchase_invoices, purchase_order)
            payment_state = _get_purchase_payment_state(payment_entries, purchase_invoices)

            steps["purchase_receipt"]["summary"] = receipt_state["summary"]
            steps["purchase_invoice"]["summary"] = invoice_state["summary"]
            steps["outgoing_payment"]["summary"] = payment_state["summary"]

            if not receipt_state["complete"]:
                current_key = "purchase_receipt"
                steps["purchase_receipt"]["status"] = "current"
                next_step = receipt_state["next_step"]
            elif not invoice_state["complete"]:
                steps["purchase_receipt"]["status"] = "complete"
                current_key = "purchase_invoice"
                steps["purchase_invoice"]["status"] = "current"
                next_step = invoice_state["next_step"]
            elif not payment_state["complete"]:
                steps["purchase_receipt"]["status"] = "complete"
                steps["purchase_invoice"]["status"] = "complete"
                current_key = "outgoing_payment"
                steps["outgoing_payment"]["status"] = "current"
                next_step = payment_state["next_step"]
            else:
                for step in PURCHASE_FLOW_STEPS:
                    steps[step["key"]]["status"] = "complete"
                current_key = "outgoing_payment"
                flow_status = "complete"
                flow_message = "Luồng mua hàng đã hoàn tất."

    _fill_remaining_statuses(steps, PURCHASE_FLOW_STEPS)

    return _build_response(
        flow_type="purchase",
        anchor_doctype=anchor_doctype,
        anchor_name=anchor_name,
        steps=steps,
        step_order=PURCHASE_FLOW_STEPS,
        current_key=current_key,
        next_step=next_step,
        flow_status=flow_status,
        flow_message=flow_message,
        overview={
            "company_flow": "Purchase",
            "party": purchase_order.get("supplier") if purchase_order else None,
            "receipt_status": purchase_order.get("status") if purchase_order else None,
            "billing_status": purchase_order.get("per_billed") if purchase_order is not None else None,
        },
    )


def _build_stock_entry_flow(context, anchor_doctype, anchor_name):
    stock_entry = frappe.get_doc("Stock Entry", context["stock_entry"])
    status = _docstatus_label(stock_entry.docstatus)
    if stock_entry.docstatus == 1:
        flow_status = "complete"
        current_key = "stock_entry"
        next_step = {"title": "Flow Completed", "detail": "Stock Entry này đã được submit."}
        step_status = "complete"
        summary = f"{stock_entry.stock_entry_type or stock_entry.purpose or 'Stock Entry'} đã được submit."
    else:
        flow_status = "active"
        current_key = "stock_entry"
        next_step = {"title": "Submit Stock Entry", "detail": "Kiểm tra kho nguồn/đích rồi submit chứng từ."}
        step_status = "current"
        summary = f"{stock_entry.stock_entry_type or stock_entry.purpose or 'Stock Entry'} đang ở trạng thái {status}."

    steps = {
        "stock_entry": {
            "key": "stock_entry",
            "title": "Stock Entry",
            "description": "Nhập xuất điều chuyển kho",
            "status": step_status,
            "summary": summary,
            "documents": [
                _serialize_reference(
                    {
                        "doctype": "Stock Entry",
                        "name": stock_entry.name,
                        "status": status,
                        "docstatus": stock_entry.docstatus,
                        "date": stock_entry.posting_date,
                        "meta": stock_entry.stock_entry_type or stock_entry.purpose,
                    },
                    anchor_doctype,
                    anchor_name,
                )
            ],
        }
    }

    return _build_response(
        flow_type="stock",
        anchor_doctype=anchor_doctype,
        anchor_name=anchor_name,
        steps=steps,
        step_order=[{"key": "stock_entry"}],
        current_key=current_key,
        next_step=next_step,
        flow_status=flow_status,
        flow_message=summary if flow_status == "complete" else None,
        overview={
            "company_flow": "Stock",
            "purpose": stock_entry.stock_entry_type or stock_entry.purpose,
            "posting_date": stock_entry.posting_date,
            "status": status,
        },
    )


def _init_steps(step_defs):
    return {
        step["key"]: {
            **step,
            "status": "upcoming",
            "summary": step["description"],
            "documents": [],
        }
        for step in step_defs
    }


def _fill_remaining_statuses(steps, step_defs):
    seen_current = False
    for step in step_defs:
        key = step["key"]
        if steps[key]["status"] == "current":
            seen_current = True
            continue
        if steps[key]["status"] == "complete":
            continue
        steps[key]["status"] = "upcoming" if seen_current else steps[key]["status"]


def _build_response(*, flow_type, anchor_doctype, anchor_name, steps, step_order, current_key, next_step, flow_status, flow_message, overview):
    ordered_steps = [steps[step["key"]] for step in step_order]
    current_step = steps.get(current_key) if current_key else None
    return {
        "ok": True,
        "doctype": anchor_doctype,
        "name": anchor_name,
        "flow_type": flow_type,
        "flow_status": flow_status,
        "flow_message": flow_message,
        "current_step": {
            "key": current_step["key"],
            "title": current_step["title"],
            "summary": current_step["summary"],
            "status": current_step["status"],
        }
        if current_step
        else None,
        "next_step": next_step,
        "steps": ordered_steps,
        "overview": overview,
    }


def _get_sales_delivery_notes(sales_order_name):
    if not sales_order_name:
        return []
    names = frappe.get_all(
        "Delivery Note Item",
        filters={"against_sales_order": sales_order_name},
        pluck="parent",
    )
    return _fetch_docs(
        "Delivery Note",
        names,
        ["name", "status", "docstatus", "posting_date", "customer"],
        sort_field="posting_date",
    )


def _get_sales_invoices(sales_order_name, delivery_notes):
    names = set()
    if sales_order_name:
        names.update(
            frappe.get_all(
                "Sales Invoice Item",
                filters={"sales_order": sales_order_name},
                pluck="parent",
            )
        )
    delivery_note_names = [row["name"] for row in delivery_notes]
    if delivery_note_names:
        names.update(
            frappe.get_all(
                "Sales Invoice Item",
                filters={"delivery_note": ["in", delivery_note_names]},
                pluck="parent",
            )
        )
    return _fetch_docs(
        "Sales Invoice",
        names,
        ["name", "status", "docstatus", "posting_date", "customer", "grand_total", "rounded_total"],
        sort_field="posting_date",
    )


def _get_sales_payment_entries(sales_order_name, sales_invoices):
    reference_names = [sales_order_name, *[row["name"] for row in sales_invoices]]
    return _get_payment_entries(["Sales Order", "Sales Invoice"], reference_names)


def _get_purchase_receipts(purchase_order_name):
    if not purchase_order_name:
        return []
    names = frappe.get_all(
        "Purchase Receipt Item",
        filters={"purchase_order": purchase_order_name},
        pluck="parent",
    )
    return _fetch_docs(
        "Purchase Receipt",
        names,
        ["name", "status", "docstatus", "posting_date", "supplier"],
        sort_field="posting_date",
    )


def _get_purchase_invoices(purchase_order_name, purchase_receipts):
    names = set()
    if purchase_order_name:
        names.update(
            frappe.get_all(
                "Purchase Invoice Item",
                filters={"purchase_order": purchase_order_name},
                pluck="parent",
            )
        )
    purchase_receipt_names = [row["name"] for row in purchase_receipts]
    if purchase_receipt_names:
        names.update(
            frappe.get_all(
                "Purchase Invoice Item",
                filters={"purchase_receipt": ["in", purchase_receipt_names]},
                pluck="parent",
            )
        )
    return _fetch_docs(
        "Purchase Invoice",
        names,
        ["name", "status", "docstatus", "posting_date", "supplier", "grand_total", "rounded_total"],
        sort_field="posting_date",
    )


def _get_purchase_payment_entries(purchase_order_name, purchase_invoices):
    reference_names = [purchase_order_name, *[row["name"] for row in purchase_invoices]]
    return _get_payment_entries(["Purchase Order", "Purchase Invoice"], reference_names)


def _get_payment_entries(reference_doctypes, reference_names):
    reference_names = [name for name in reference_names if name]
    if not reference_names:
        return []

    references = frappe.get_all(
        "Payment Entry Reference",
        filters=[
            ["reference_doctype", "in", reference_doctypes],
            ["reference_name", "in", reference_names],
        ],
        fields=["parent"],
        limit_page_length=0,
    )
    return _fetch_docs(
        "Payment Entry",
        [row["parent"] for row in references],
        [
            "name",
            "docstatus",
            "payment_type",
            "party_type",
            "party",
            "posting_date",
        ],
        sort_field="posting_date",
    )


def _fetch_docs(doctype, names, fields, sort_field=None):
    unique_names = [name for name in set(names or []) if name]
    if not unique_names:
        return []
    docs = frappe.get_all(doctype, filters={"name": ["in", unique_names]}, fields=fields)
    if sort_field:
        docs.sort(key=lambda row: ((row.get(sort_field) or ""), row.get("name") or ""))
    return docs


def _get_doc_row(doctype, name, fields):
    if not name:
        return None
    rows = frappe.get_all(doctype, filters={"name": name}, fields=fields, limit_page_length=1)
    return rows[0] if rows else None


def _first_value(doctype, filters, fieldname):
    values = frappe.get_all(doctype, filters=filters, pluck=fieldname, limit_page_length=1)
    return values[0] if values else None


def _serialize_single_doc(row, doctype, anchor_doctype, anchor_name, meta_getter=None):
    if not row:
        return []
    return [
        _serialize_reference(
            {
                "doctype": doctype,
                "name": row["name"],
                "status": row.get("status") or _docstatus_label(row.get("docstatus")),
                "docstatus": row.get("docstatus"),
                "date": row.get("transaction_date") or row.get("posting_date"),
                "meta": meta_getter(row) if callable(meta_getter) else None,
            },
            anchor_doctype,
            anchor_name,
        )
    ]


def _serialize_docs(rows, doctype, anchor_doctype, anchor_name, meta_getter=None, status_getter=None):
    return [
        _serialize_reference(
            {
                "doctype": doctype,
                "name": row["name"],
                "status": status_getter(row) if callable(status_getter) else row.get("status") or _docstatus_label(row.get("docstatus")),
                "docstatus": row.get("docstatus"),
                "date": row.get("transaction_date") or row.get("posting_date"),
                "meta": meta_getter(row) if callable(meta_getter) else None,
            },
            anchor_doctype,
            anchor_name,
        )
        for row in rows
    ]


def _serialize_reference(row, anchor_doctype, anchor_name):
    return {
        "doctype": row["doctype"],
        "name": row["name"],
        "status": row.get("status") or _docstatus_label(row.get("docstatus")),
        "docstatus": row.get("docstatus"),
        "date": str(row.get("date")) if row.get("date") else None,
        "meta": row.get("meta"),
        "is_anchor": row["doctype"] == anchor_doctype and row["name"] == anchor_name,
    }


def _get_sales_quotation_summary(quotation, sales_order):
    if sales_order and quotation:
        return "Báo giá đã được chuyển thành Sales Order."
    if quotation:
        return "Đây là điểm bắt đầu của luồng bán hàng."
    return "Luồng này bắt đầu trực tiếp từ Sales Order."


def _get_sales_order_summary(sales_order):
    if not sales_order:
        return "Chưa có Sales Order nào được tạo."
    if sales_order.get("docstatus") == 0:
        return "Sales Order đang ở Draft, cần submit để giao hàng."
    return f"Sales Order đang ở trạng thái {sales_order.get('status') or 'Submitted'}."


def _get_sales_delivery_state(delivery_notes, sales_order):
    active_notes = [row for row in delivery_notes if row.get("docstatus") != 2]
    draft_notes = [row for row in active_notes if row.get("docstatus") == 0]
    submitted_notes = [row for row in active_notes if row.get("docstatus") == 1]
    delivered = sales_order and (
        (sales_order.get("per_delivered") or 0) >= 100
        or sales_order.get("delivery_status") == "Fully Delivered"
    )

    if delivered and submitted_notes:
        return {"complete": True, "summary": f"Đã giao đủ qua {len(submitted_notes)} Delivery Note.", "next_step": None}
    if draft_notes:
        return {
            "complete": False,
            "summary": f"Có {len(draft_notes)} Delivery Note draft đang chờ submit.",
            "next_step": {"title": "Submit Delivery Note", "detail": f"Submit {draft_notes[0]['name']} để xác nhận xuất kho."},
        }
    if submitted_notes:
        return {
            "complete": False,
            "summary": f"Đã có {len(submitted_notes)} Delivery Note nhưng đơn vẫn chưa giao đủ.",
            "next_step": {"title": "Create next Delivery Note", "detail": "Tạo Delivery Note cho phần hàng còn lại."},
        }
    return {
        "complete": False,
        "summary": "Chưa có Delivery Note nào được tạo.",
        "next_step": {"title": "Create Delivery Note", "detail": "Tạo Delivery Note để bắt đầu xuất kho."},
    }


def _get_sales_invoice_state(sales_invoices, sales_order):
    active_invoices = [row for row in sales_invoices if row.get("docstatus") != 2]
    draft_invoices = [row for row in active_invoices if row.get("docstatus") == 0]
    submitted_invoices = [row for row in active_invoices if row.get("docstatus") == 1]
    billed = sales_order and (
        (sales_order.get("per_billed") or 0) >= 100
        or sales_order.get("billing_status") == "Fully Billed"
    )

    if billed and submitted_invoices:
        return {"complete": True, "summary": f"Đã xuất đủ {len(submitted_invoices)} Sales Invoice.", "next_step": None}
    if draft_invoices:
        return {
            "complete": False,
            "summary": f"Có {len(draft_invoices)} Sales Invoice draft đang chờ submit.",
            "next_step": {"title": "Submit Sales Invoice", "detail": f"Submit {draft_invoices[0]['name']} để ghi nhận doanh thu."},
        }
    if submitted_invoices:
        return {
            "complete": False,
            "summary": f"Đã có {len(submitted_invoices)} Sales Invoice nhưng đơn vẫn chưa bill đủ.",
            "next_step": {"title": "Create next Sales Invoice", "detail": "Lập thêm Sales Invoice cho phần còn lại."},
        }
    return {
        "complete": False,
        "summary": "Chưa có Sales Invoice nào được tạo.",
        "next_step": {"title": "Create Sales Invoice", "detail": "Tạo Sales Invoice để tiếp tục luồng bán hàng."},
    }


def _get_sales_payment_state(payment_entries, sales_invoices):
    submitted_payments = [row for row in payment_entries if row.get("docstatus") == 1]
    if _all_invoices_paid(sales_invoices):
        return {"complete": True, "summary": f"Đã thu tiền qua {len(submitted_payments)} Payment Entry.", "next_step": None}
    if submitted_payments:
        return {
            "complete": False,
            "summary": f"Đã có {len(submitted_payments)} Payment Entry nhưng vẫn còn công nợ mở.",
            "next_step": {"title": "Allocate remaining payment", "detail": "Phân bổ hoặc ghi nhận thêm khoản thu còn thiếu."},
        }
    return {
        "complete": False,
        "summary": "Chưa có Payment Entry thu tiền nào cho luồng này.",
        "next_step": {"title": "Create Payment Entry", "detail": "Ghi nhận incoming payment để hoàn tất luồng bán hàng."},
    }


def _get_material_request_summary(material_request, purchase_order):
    if purchase_order and material_request:
        return "Material Request đã được chuyển thành Purchase Order."
    if material_request:
        return "Đây là điểm khởi đầu của luồng mua hàng."
    return "Luồng này bắt đầu trực tiếp từ Purchase Order."


def _get_purchase_order_summary(purchase_order):
    if not purchase_order:
        return "Chưa có Purchase Order nào được tạo."
    if purchase_order.get("docstatus") == 0:
        return "Purchase Order đang ở Draft, cần submit để nhận hàng."
    return f"Purchase Order đang ở trạng thái {purchase_order.get('status') or 'Submitted'}."


def _get_purchase_receipt_state(purchase_receipts, purchase_order):
    active_receipts = [row for row in purchase_receipts if row.get("docstatus") != 2]
    draft_receipts = [row for row in active_receipts if row.get("docstatus") == 0]
    submitted_receipts = [row for row in active_receipts if row.get("docstatus") == 1]
    fully_received = purchase_order and (purchase_order.get("per_received") or 0) >= 100

    if fully_received and submitted_receipts:
        return {"complete": True, "summary": f"Đã nhận đủ qua {len(submitted_receipts)} Purchase Receipt.", "next_step": None}
    if draft_receipts:
        return {
            "complete": False,
            "summary": f"Có {len(draft_receipts)} Purchase Receipt draft đang chờ submit.",
            "next_step": {"title": "Submit Purchase Receipt", "detail": f"Submit {draft_receipts[0]['name']} để nhập kho."},
        }
    if submitted_receipts:
        return {
            "complete": False,
            "summary": f"Đã nhận một phần qua {len(submitted_receipts)} Purchase Receipt.",
            "next_step": {"title": "Create next Purchase Receipt", "detail": "Tạo thêm phiếu nhập cho phần hàng còn lại."},
        }
    return {
        "complete": False,
        "summary": "Chưa có Purchase Receipt nào được tạo.",
        "next_step": {"title": "Create Purchase Receipt", "detail": "Tạo Purchase Receipt khi hàng về kho."},
    }


def _get_purchase_invoice_state(purchase_invoices, purchase_order):
    active_invoices = [row for row in purchase_invoices if row.get("docstatus") != 2]
    draft_invoices = [row for row in active_invoices if row.get("docstatus") == 0]
    submitted_invoices = [row for row in active_invoices if row.get("docstatus") == 1]
    fully_billed = purchase_order and (purchase_order.get("per_billed") or 0) >= 100

    if fully_billed and submitted_invoices:
        return {"complete": True, "summary": f"Đã ghi nhận đủ {len(submitted_invoices)} Purchase Invoice.", "next_step": None}
    if draft_invoices:
        return {
            "complete": False,
            "summary": f"Có {len(draft_invoices)} Purchase Invoice draft đang chờ submit.",
            "next_step": {"title": "Submit Purchase Invoice", "detail": f"Submit {draft_invoices[0]['name']} để ghi nhận công nợ."},
        }
    if submitted_invoices:
        return {
            "complete": False,
            "summary": f"Đã có {len(submitted_invoices)} Purchase Invoice nhưng PO chưa bill đủ.",
            "next_step": {"title": "Create next Purchase Invoice", "detail": "Lập thêm Purchase Invoice cho phần còn lại."},
        }
    return {
        "complete": False,
        "summary": "Chưa có Purchase Invoice nào được tạo.",
        "next_step": {"title": "Create Purchase Invoice", "detail": "Tạo Purchase Invoice để tiếp tục luồng mua hàng."},
    }


def _get_purchase_payment_state(payment_entries, purchase_invoices):
    submitted_payments = [row for row in payment_entries if row.get("docstatus") == 1]
    if _all_invoices_paid(purchase_invoices):
        return {"complete": True, "summary": f"Đã thanh toán qua {len(submitted_payments)} Payment Entry.", "next_step": None}
    if submitted_payments:
        return {
            "complete": False,
            "summary": f"Đã có {len(submitted_payments)} Payment Entry nhưng vẫn còn số tiền chưa thanh toán.",
            "next_step": {"title": "Allocate remaining payment", "detail": "Thanh toán hoặc phân bổ phần công nợ còn thiếu."},
        }
    return {
        "complete": False,
        "summary": "Chưa có Payment Entry thanh toán nào cho luồng này.",
        "next_step": {"title": "Create Payment Entry", "detail": "Tạo Payment Entry để thanh toán nhà cung cấp."},
    }


def _all_invoices_paid(invoices):
    return bool(invoices) and all(row.get("status") == "Paid" for row in invoices if row.get("docstatus") == 1)


def _format_currency_hint(row):
    amount = row.get("rounded_total") or row.get("grand_total")
    if amount is None:
        return row.get("status")
    return f"{row.get('status') or 'Invoice'} · {frappe.format_value(amount, {'fieldtype': 'Currency'})}"


def _get_payment_status(row):
    if row.get("docstatus") == 0:
        return "Draft"
    if row.get("docstatus") == 2:
        return "Cancelled"
    if row.get("payment_type") == "Receive":
        return "Received"
    if row.get("payment_type") == "Pay":
        return "Paid"
    return row.get("payment_type") or "Submitted"


def _docstatus_label(docstatus):
    return {0: "Draft", 1: "Submitted", 2: "Cancelled"}.get(docstatus, "Unknown")

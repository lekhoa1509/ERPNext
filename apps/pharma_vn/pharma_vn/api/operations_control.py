import frappe
from frappe import _
from frappe.utils import now_datetime

from pharma_vn.services.capa import build_capa_values, build_deviation_values
from pharma_vn.services.state_machine import build_transition_audit, get_next_states
from pharma_vn.services.traceability import summarize_traceability
from pharma_vn.utils.batch import update_batch_fields
from pharma_vn.utils.response import ok
from pharma_vn.utils.validation import get_json_payload, require_fields


@frappe.whitelist()
def transition_batch_state(payload=None):
    data = get_json_payload(payload)
    require_fields(data, ["batch_no", "next_state"])

    current_state = frappe.db.get_value("Batch", data["batch_no"], "batch_status") or "Draft"
    audit = build_transition_audit(
        "batch",
        current_state,
        data["next_state"],
        frappe.session.user,
        note=data.get("note"),
    )
    update_values = {"batch_status": audit["to_state"]}
    if audit["to_state"] == "Released":
        update_values["release_date"] = now_datetime()
        update_values["released_by"] = frappe.session.user
    update_batch_fields(data["batch_no"], update_values)

    return ok(
        _("Batch state updated"),
        {
            "batch_no": data["batch_no"],
            "from_state": audit["from_state"],
            "to_state": audit["to_state"],
            "allowed_next_states": get_next_states("batch", audit["to_state"]),
        },
    )


@frappe.whitelist()
def transition_recall_state(payload=None):
    data = get_json_payload(payload)
    require_fields(data, ["recall_case", "next_state"])

    recall_doc = frappe.get_doc("PH Recall Case", data["recall_case"])
    current_state = recall_doc.status or "Open"
    audit = build_transition_audit(
        "recall",
        current_state,
        data["next_state"],
        frappe.session.user,
        note=data.get("note"),
    )
    recall_doc.status = audit["to_state"]
    if hasattr(recall_doc, "assigned_to") and data.get("assigned_to"):
        recall_doc.assigned_to = data["assigned_to"]
    if hasattr(recall_doc, "investigation_summary") and data.get("investigation_summary"):
        recall_doc.investigation_summary = data["investigation_summary"]
    recall_doc.add_comment(
        "Comment",
        f"State transition {audit['from_state']} -> {audit['to_state']} by {frappe.session.user}. {data.get('note') or ''}".strip(),
    )
    recall_doc.save(ignore_permissions=True)

    return ok(
        _("Recall state updated"),
        {
            "recall_case": recall_doc.name,
            "from_state": audit["from_state"],
            "to_state": audit["to_state"],
            "allowed_next_states": get_next_states("recall", audit["to_state"]),
        },
    )


@frappe.whitelist()
def get_batch_traceability(payload=None):
    data = get_json_payload(payload)
    batch_no = data.get("batch_no") or frappe.form_dict.get("batch_no")
    if not batch_no:
        frappe.throw(_("batch_no is required"))

    incoming_rows = frappe.db.sql(
        """
        select pri.parent as purchase_receipt, pr.supplier, pr.posting_date, pri.item_code, pri.qty
        from `tabPurchase Receipt Item` pri
        inner join `tabPurchase Receipt` pr on pr.name = pri.parent
        where pr.docstatus = 1 and pri.batch_no = %(batch_no)s
        order by pr.posting_date asc, pri.parent asc
        """,
        {"batch_no": batch_no},
        as_dict=True,
    )
    outgoing_rows = frappe.db.sql(
        """
        select dni.parent as delivery_note, dn.customer, dn.posting_date, dni.item_code, dni.qty
        from `tabDelivery Note Item` dni
        inner join `tabDelivery Note` dn on dn.name = dni.parent
        where dn.docstatus = 1 and dni.batch_no = %(batch_no)s
        order by dn.posting_date asc, dni.parent asc
        """,
        {"batch_no": batch_no},
        as_dict=True,
    )
    invoice_rows = frappe.db.sql(
        """
        select sii.parent as sales_invoice, si.customer, si.posting_date, sii.item_code, sii.qty
        from `tabSales Invoice Item` sii
        inner join `tabSales Invoice` si on si.name = sii.parent
        where si.docstatus = 1 and sii.batch_no = %(batch_no)s
        order by si.posting_date asc, sii.parent asc
        """,
        {"batch_no": batch_no},
        as_dict=True,
    )
    summary = summarize_traceability(
        batch_no=batch_no,
        batch_status=frappe.db.get_value("Batch", batch_no, "batch_status"),
        incoming_rows=incoming_rows,
        outgoing_rows=outgoing_rows,
    )

    return ok(
        _("Batch traceability loaded"),
        {
            "summary": summary,
            "backward_trace": incoming_rows,
            "forward_trace": outgoing_rows,
            "invoice_trace": invoice_rows,
        },
    )


@frappe.whitelist()
def create_deviation(payload=None):
    data = get_json_payload(payload)
    require_fields(data, ["title"])
    values = build_deviation_values(data, reported_by=frappe.session.user)
    doc = frappe.get_doc({"doctype": "PH Deviation", **values})
    doc.insert(ignore_permissions=True)
    return ok(_("Deviation created"), {"name": doc.name, "status": doc.status})


@frappe.whitelist()
def create_capa(payload=None):
    data = get_json_payload(payload)
    require_fields(data, ["title"])
    values = build_capa_values(data, created_by=frappe.session.user)
    doc = frappe.get_doc({"doctype": "PH CAPA", **values})
    doc.insert(ignore_permissions=True)
    return ok(_("CAPA created"), {"name": doc.name, "status": doc.status})

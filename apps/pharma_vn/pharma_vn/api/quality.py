import frappe
from frappe import _
from frappe.utils import now_datetime

from pharma_vn.services.quality import build_batch_release_values
from pharma_vn.services.state_machine import validate_transition
from pharma_vn.utils.batch import update_batch_fields
from pharma_vn.utils.response import ok
from pharma_vn.utils.validation import get_json_payload, require_fields


@frappe.whitelist()
def release_batch(payload=None):
    data = get_json_payload(payload)
    require_fields(data, ["batch_no", "item_code", "decision"])
    try:
        # Service lo phan chuan hoa rule; API chi con vai tro validate input va ghi chung tu.
        release_plan = build_batch_release_values(
            data,
            current_user=frappe.session.user,
            release_timestamp=now_datetime(),
        )
    except ValueError as exc:
        frappe.throw(_(str(exc)))

    release_doc = frappe.get_doc(
        {
            "doctype": "PH Batch Release",
            **release_plan["release_values"],
        }
    )
    release_doc.insert(ignore_permissions=True)

    if data.get("submit", True):
        release_doc.submit()

    # Batch la doi tuong duoc dung o flow ban hang, nen cap nhat ngay sau khi co quyet dinh QA.
    update_batch_fields(data["batch_no"], release_plan["batch_updates"])

    return ok(
        _("Batch decision recorded"),
        {
            "batch_no": data["batch_no"],
            "release_document": release_doc.name,
            "status": release_plan["decision"],
        },
    )


@frappe.whitelist()
def send_batch_to_qa(payload=None):
    data = get_json_payload(payload)
    require_fields(data, ["batch_no"])
    current_state = frappe.db.get_value("Batch", data["batch_no"], "batch_status") or "Draft"
    try:
        validate_transition("batch", current_state, "QA")
    except ValueError as exc:
        frappe.throw(_(str(exc)))

    update_batch_fields(
        data["batch_no"],
        {
            "batch_status": "QA",
            "batch_workflow_note": data.get("note") or "Moved to QA review.",
        },
    )
    return ok(
        _("Batch moved to QA"),
        {"batch_no": data["batch_no"], "from_state": current_state, "to_state": "QA"},
    )

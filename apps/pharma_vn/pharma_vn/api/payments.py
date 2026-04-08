import frappe
from frappe import _
from frappe.utils import flt, getdate, nowdate

from pharma_vn.utils.response import ok
from pharma_vn.utils.validation import get_json_payload, require_fields


@frappe.whitelist(allow_guest=True)
def vnpay_callback(payload=None):
    data = get_json_payload(payload)
    require_fields(data, ["reference_name", "amount", "status", "gateway_transaction_no"])

    invoice = frappe.get_doc("Sales Invoice", data["reference_name"])
    status = str(data["status"]).lower()
    amount = flt(data["amount"])

    invoice.add_comment(
        "Comment",
        _("Gateway callback received: {0} / amount {1}").format(
            data["gateway_transaction_no"], amount
        ),
    )

    if frappe.db.has_column("Sales Invoice", "payment_gateway_txn_id"):
        frappe.db.set_value(
            "Sales Invoice",
            invoice.name,
            "payment_gateway_txn_id",
            data["gateway_transaction_no"],
            update_modified=True,
        )

    if status not in {"success", "paid", "00"}:
        return ok(_("Payment callback recorded"), {"status": status, "payment_entry": None})

    payment_entry_name = None
    if data.get("create_payment_entry") and data.get("paid_to_account"):
        payment_entry_name = _create_payment_entry(invoice, amount, data)

    return ok(
        _("Payment processed"),
        {
            "status": status,
            "payment_entry": payment_entry_name,
            "reference_name": invoice.name,
        },
    )


def _create_payment_entry(invoice, amount, data):
    payment_entry = frappe.get_doc(
        {
            "doctype": "Payment Entry",
            "payment_type": "Receive",
            "posting_date": data.get("posting_date") or nowdate(),
            "company": invoice.company,
            "mode_of_payment": data.get("mode_of_payment"),
            "party_type": "Customer",
            "party": invoice.customer,
            "paid_from": invoice.debit_to,
            "paid_to": data["paid_to_account"],
            "paid_amount": amount,
            "received_amount": amount,
            "reference_no": data["gateway_transaction_no"],
            "reference_date": getdate(data.get("reference_date") or nowdate()),
            "references": [
                {
                    "reference_doctype": "Sales Invoice",
                    "reference_name": invoice.name,
                    "allocated_amount": amount,
                    "total_amount": invoice.grand_total,
                    "outstanding_amount": invoice.outstanding_amount,
                }
            ],
        }
    )
    payment_entry.insert(ignore_permissions=True)

    if data.get("submit_payment_entry"):
        payment_entry.submit()

    return payment_entry.name


import frappe
from frappe import _
from frappe.utils import nowdate

from pharma_vn.utils.response import ok
from pharma_vn.utils.validation import get_json_payload, require_fields


@frappe.whitelist()
def create_b2b_order(payload=None):
    data = get_json_payload(payload)
    require_fields(data, ["customer", "company", "items"])

    order = frappe.new_doc("Sales Order")
    order.customer = data["customer"]
    order.company = data["company"]
    order.transaction_date = data.get("transaction_date") or nowdate()
    order.set_warehouse = data.get("set_warehouse")
    order.po_no = data.get("customer_po_no")
    order.po_date = data.get("customer_po_date")
    order.pharma_external_reference = data.get("external_reference")
    order.pharma_order_description = data.get("description")
    order.pharma_requested_date = data.get("requested_date")
    order.pharma_issue_date = data.get("issue_date")
    order.pharma_origin = data.get("origin")
    order.pharma_distribution_channel = data.get("distribution_channel")
    order.pharma_sales_organization = data.get("sales_organization")
    order.pharma_sales_unit = data.get("sales_unit")
    order.pharma_payment_reference_type = data.get("payment_reference_type")
    order.pharma_send_order_confirmation = data.get("send_order_confirmation", 0)

    for row in data["items"]:
        require_fields(row, ["item_code", "qty"])
        order.append(
            "items",
            {
                "item_code": row["item_code"],
                "qty": row["qty"],
                "rate": row.get("rate", 0),
                "warehouse": row.get("warehouse") or data.get("set_warehouse"),
                "delivery_date": row.get("delivery_date") or data.get("delivery_date") or nowdate(),
            },
        )

    order.flags.ignore_permissions = True
    order.run_method("set_missing_values")
    order.run_method("calculate_taxes_and_totals")
    order.save()

    if data.get("submit"):
        order.submit()

    return ok(
        _("Sales Order created"),
        {"doctype": order.doctype, "name": order.name, "docstatus": order.docstatus},
    )

import frappe
from frappe import _

from pharma_vn.services.compliance import build_e_invoice_payload, evaluate_sales_invoice_guardrails
from pharma_vn.utils.response import ok
from pharma_vn.utils.validation import get_json_payload


@frappe.whitelist()
def review_sales_invoice(payload=None):
    data = get_json_payload(payload)
    review = evaluate_sales_invoice_guardrails(data)
    return ok(_("Sales Invoice compliance reviewed"), review)


@frappe.whitelist()
def build_sales_e_invoice(payload=None):
    data = get_json_payload(payload)
    return ok(_("E-invoice payload prepared"), build_e_invoice_payload(data))

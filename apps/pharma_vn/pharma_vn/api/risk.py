import frappe
from frappe.utils import cint

from pharma_vn.risk_assessment.service import (
    check_customer_risk,
    get_customer_risk_snapshot,
    quick_create_customer_from_tax_id,
)


@frappe.whitelist()
def check(customer=None, tax_code=None, force_refresh=0):
    return check_customer_risk(
        customer=customer,
        tax_code=tax_code,
        force_refresh=cint(force_refresh),
    )


@frappe.whitelist()
def get_customer_risk(customer):
    return get_customer_risk_snapshot(customer)


@frappe.whitelist()
def quick_create_customer(tax_code=None, customer_type="Company"):
    return quick_create_customer_from_tax_id(
        tax_code=tax_code,
        customer_type=customer_type,
    )

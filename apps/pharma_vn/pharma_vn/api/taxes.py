import frappe

from pharma_vn.automation.transaction_taxes import _build_item_tax_map
from pharma_vn.setup.taxes import (
    PURCHASE_DIRECTION,
    SALES_DIRECTION,
    ensure_vietnam_tax_setup,
    normalize_vat_rate,
    resolve_item_tax_template_name,
)


DOCTYPE_DIRECTION = {
    "Quotation": SALES_DIRECTION,
    "Sales Order": SALES_DIRECTION,
    "Delivery Note": SALES_DIRECTION,
    "Sales Invoice": SALES_DIRECTION,
    "Purchase Order": PURCHASE_DIRECTION,
    "Purchase Receipt": PURCHASE_DIRECTION,
    "Purchase Invoice": PURCHASE_DIRECTION,
}


@frappe.whitelist()
def get_item_vat_choice(company, parent_doctype, vat_rate):
    ensure_vietnam_tax_setup()

    direction = DOCTYPE_DIRECTION.get(parent_doctype)
    if not direction:
        frappe.throw(f"Unsupported doctype for VAT setup: {parent_doctype}")

    rate = normalize_vat_rate(vat_rate)
    template = resolve_item_tax_template_name(
        company=company,
        direction=direction,
        vat_rate=rate,
    )
    return {
        "vat_rate": rate,
        "item_tax_template": template,
        "item_tax_rate": frappe.as_json(_build_item_tax_map(template)),
    }

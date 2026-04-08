import json

import frappe

from pharma_vn.setup.taxes import (
    PURCHASE_DIRECTION,
    SALES_DIRECTION,
    ensure_vietnam_tax_setup,
    normalize_vat_rate,
    resolve_item_tax_template_name,
)


ITEM_DOCTYPES = {
    "Quotation": SALES_DIRECTION,
    "Sales Order": SALES_DIRECTION,
    "Delivery Note": SALES_DIRECTION,
    "Sales Invoice": SALES_DIRECTION,
    "Purchase Order": PURCHASE_DIRECTION,
    "Purchase Receipt": PURCHASE_DIRECTION,
    "Purchase Invoice": PURCHASE_DIRECTION,
}

MANAGED_VAT_ACCOUNTS = tuple(
    f"{prefix}{rate}" for prefix in ("3331", "1331") for rate in ("5", "8", "10")
)


def sync_transaction_taxes(doc, method=None):
    direction = ITEM_DOCTYPES.get(doc.doctype)
    if not direction or not doc.company or not doc.get("items"):
        return

    ensure_vietnam_tax_setup()

    uses_item_vat = False
    tax_rows = {}

    for row in doc.items:
        vat_rate = _resolve_row_vat_rate(doc, row, direction)
        row.pharma_vat_rate = str(vat_rate)

        if vat_rate == 0:
            row.item_tax_template = None
            row.item_tax_rate = "{}"
            continue

        uses_item_vat = True
        row.item_tax_template = resolve_item_tax_template_name(
            company=doc.company,
            direction=direction,
            vat_rate=vat_rate,
        )
        item_tax_map = _build_item_tax_map(row.item_tax_template)
        row.item_tax_rate = frappe.as_json(item_tax_map)

        for account_head in item_tax_map:
            tax_rows[account_head] = _make_tax_row(account_head)

    if not uses_item_vat:
        return

    if hasattr(doc, "taxes_and_charges"):
        doc.taxes_and_charges = None

    preserved_rows = []
    for tax in doc.get("taxes") or []:
        account_head = tax.get("account_head")
        if tax.get("set_by_item_tax_template"):
            continue
        if tax.get("charge_type") == "On Net Total" and _is_managed_vat_account(account_head):
            continue
        preserved_rows.append(_clone_tax_row(tax))

    doc.set("taxes", preserved_rows + list(tax_rows.values()))

    if hasattr(doc, "calculate_taxes_and_totals"):
        doc.calculate_taxes_and_totals()


def _resolve_row_vat_rate(doc, row, direction):
    current_value = row.get("pharma_vat_rate")
    if current_value not in (None, ""):
        return normalize_vat_rate(current_value)

    row_tax_rate = _extract_row_tax_rate(row)
    if row_tax_rate is not None:
        return row_tax_rate

    item_field = "pharma_default_sales_vat_rate" if direction == SALES_DIRECTION else "pharma_default_purchase_vat_rate"
    item_default = frappe.db.get_value("Item", row.item_code, item_field) if row.item_code else None
    if item_default not in (None, ""):
        return normalize_vat_rate(item_default)

    return 10


def _extract_row_tax_rate(row):
    payload = row.get("item_tax_rate")
    if not payload:
        return None

    try:
        tax_map = json.loads(payload) if isinstance(payload, str) else payload
    except Exception:
        return None

    non_zero_rates = sorted({normalize_vat_rate(rate) for rate in tax_map.values() if float(rate or 0)})
    if len(non_zero_rates) == 1:
        return non_zero_rates[0]
    return None


def _build_item_tax_map(template_name):
    if not template_name:
        return {}

    template = frappe.get_cached_doc("Item Tax Template", template_name)
    return {row.tax_type: float(row.tax_rate or 0) for row in template.taxes}


def _make_tax_row(account_head):
    return frappe._dict(
        {
            "charge_type": "On Net Total",
            "account_head": account_head,
            "rate": 0,
            "description": str(account_head).split(" - ")[0],
            "set_by_item_tax_template": 1,
            "category": "Total",
            "add_deduct_tax": "Add",
        }
    )


def _clone_tax_row(row):
    fields = {
        "charge_type",
        "account_head",
        "description",
        "included_in_print_rate",
        "cost_center",
        "rate",
        "account_currency",
        "tax_amount",
        "total",
        "tax_amount_after_discount_amount",
        "category",
        "add_deduct_tax",
        "row_id",
        "tax_amount_for_current_item",
        "grand_total_for_current_item",
        "tax_fraction_for_current_item",
        "grand_total_fraction_for_current_item",
    }
    return frappe._dict({field: row.get(field) for field in fields if row.get(field) is not None})


def _is_managed_vat_account(account_head):
    return bool(account_head and any(part in account_head for part in MANAGED_VAT_ACCOUNTS))

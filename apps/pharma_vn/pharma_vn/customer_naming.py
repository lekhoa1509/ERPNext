import re

import frappe
from frappe import _
from frappe.model.naming import make_autoname
from frappe.utils import cstr


CUSTOMER_NAMING_SERIES = "CM-.####"
CUSTOMER_NAME_PATTERN = re.compile(r"^CM-\d{4,}$")


def generate_customer_id(make_name=None):
    generator = make_name or make_autoname
    return generator(CUSTOMER_NAMING_SERIES)


def apply_customer_naming(doc, make_name=None):
    if hasattr(doc, "naming_series"):
        doc.naming_series = CUSTOMER_NAMING_SERIES

    current_name = str(getattr(doc, "name", "") or "").strip()
    if CUSTOMER_NAME_PATTERN.fullmatch(current_name):
        return current_name

    doc.name = generate_customer_id(make_name=make_name)
    return doc.name


def ensure_unique_customer_identity(doc):
    normalized_tax_id = normalize_tax_id(getattr(doc, "tax_id", ""))
    if hasattr(doc, "tax_id"):
        doc.tax_id = normalized_tax_id
    if hasattr(doc, "tax_code") and normalized_tax_id:
        doc.tax_code = normalized_tax_id

    existing_tax_customer = find_existing_customer_by_tax_id(normalized_tax_id, current_name=getattr(doc, "name", ""))
    if existing_tax_customer:
        customer_label = existing_tax_customer.get("customer_name") or existing_tax_customer.get("name")
        frappe.throw(
            _("Tax ID / MST {0} already belongs to Customer {1}. Please use the existing customer instead of creating a new one.").format(
                normalized_tax_id,
                customer_label,
            )
        )

    customer_name = cstr(getattr(doc, "customer_name", "")).strip()
    existing_name_customer = find_existing_customer_by_name(customer_name, current_name=getattr(doc, "name", ""))
    if existing_name_customer:
        customer_label = existing_name_customer.get("customer_name") or existing_name_customer.get("name")
        frappe.throw(
            _("Customer name {0} already exists as {1}. Please review the existing customer instead of creating a duplicate.").format(
                customer_name,
                customer_label,
            )
        )


def find_existing_customer_by_tax_id(tax_id, current_name=""):
    normalized_tax_id = normalize_tax_id(tax_id)
    if not normalized_tax_id:
        return None

    for fieldname in ("tax_id", "tax_code"):
        if fieldname == "tax_code" and not _customer_has_field(fieldname):
            continue
        existing = _find_customer({fieldname: normalized_tax_id}, current_name=current_name)
        if existing:
            return existing
    return None


def find_existing_customer_by_name(customer_name, current_name=""):
    normalized_name = cstr(customer_name).strip()
    if not normalized_name:
        return None
    return _find_customer({"customer_name": normalized_name}, current_name=current_name)


def normalize_tax_id(value):
    return cstr(value).strip().replace(" ", "").upper()


def _find_customer(filters, current_name=""):
    query_filters = dict(filters)
    current_name = cstr(current_name).strip()
    if current_name:
        query_filters["name"] = ["!=", current_name]
    rows = frappe.get_all(
        "Customer",
        filters=query_filters,
        fields=["name", "customer_name"],
        limit_page_length=1,
    )
    return rows[0] if rows else None


def _customer_has_field(fieldname):
    try:
        return bool(frappe.db.has_column("Customer", fieldname))
    except Exception:
        return False

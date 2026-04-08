import frappe

from pharma_vn.setup.bootstrap_demo import bootstrap_vietnam_demo


KEEP_COMPANY_FALLBACK = "Công Ty Cổ Phần Dược Phẩm OPC"
DEMO_ITEM_CODES = tuple(f"SKU{i:03d}" for i in range(1, 11))
DEMO_CUSTOMERS = (
    "Grant Plastics Ltd.",
    "West View Software Ltd.",
    "Palmer Productions Ltd.",
)
DEMO_SUPPLIERS = (
    "Zuckerman Security Ltd.",
    "MA Inc.",
    "Summit Traders Ltd.",
)
DEMO_GROUPS = (
    ("Item Group", "Demo Item Group"),
    ("Customer Group", "Demo Customer Group"),
    ("Supplier Group", "Demo Supplier Group"),
)


def cleanup_non_pharma_demo(keep_company=None):
    keep_company = keep_company or _resolve_keep_company()
    _set_keep_company_defaults(keep_company)

    _delete_demo_items()
    _delete_demo_customers()
    _delete_demo_suppliers()
    _delete_demo_groups()
    _delete_extra_companies(keep_company)

    bootstrap_vietnam_demo()
    frappe.db.commit()


def _resolve_keep_company():
    default_company = frappe.db.get_single_value("Global Defaults", "default_company")
    if default_company and frappe.db.exists("Company", default_company):
        return default_company

    if frappe.db.exists("Company", KEEP_COMPANY_FALLBACK):
        return KEEP_COMPANY_FALLBACK

    companies = frappe.get_all("Company", fields=["name"], order_by="creation asc")
    if companies:
        return companies[0].name

    return KEEP_COMPANY_FALLBACK


def _set_keep_company_defaults(company):
    frappe.db.set_single_value("Global Defaults", "default_company", company)


def _delete_demo_items():
    for item_code in DEMO_ITEM_CODES:
        if not frappe.db.exists("Item", item_code):
            continue

        for batch in frappe.get_all("Batch", filters={"item": item_code}, pluck="name"):
            frappe.delete_doc("Batch", batch, ignore_permissions=True, force=True)

        for item_price in frappe.get_all("Item Price", filters={"item_code": item_code}, pluck="name"):
            frappe.delete_doc("Item Price", item_price, ignore_permissions=True, force=True)

        frappe.delete_doc("Item", item_code, ignore_permissions=True, force=True)


def _delete_demo_customers():
    for customer in DEMO_CUSTOMERS:
        if frappe.db.exists("Customer", customer):
            frappe.delete_doc("Customer", customer, ignore_permissions=True, force=True)


def _delete_demo_suppliers():
    for supplier in DEMO_SUPPLIERS:
        if frappe.db.exists("Supplier", supplier):
            frappe.delete_doc("Supplier", supplier, ignore_permissions=True, force=True)


def _delete_demo_groups():
    for doctype, docname in DEMO_GROUPS:
        if frappe.db.exists(doctype, docname):
            frappe.delete_doc(doctype, docname, ignore_permissions=True, force=True)


def _delete_extra_companies(keep_company):
    extra_companies = [
        company.name
        for company in frappe.get_all("Company", fields=["name"], order_by="creation asc")
        if company.name != keep_company
    ]

    for company in extra_companies:
        _delete_company_dependent_docs(company)
        if frappe.db.exists("Company", company):
            frappe.delete_doc("Company", company, ignore_permissions=True, force=True)


def _delete_company_dependent_docs(company):
    for doctype in (
        "Sales Taxes and Charges Template",
        "Purchase Taxes and Charges Template",
    ):
        for docname in frappe.get_all(doctype, filters={"company": company}, pluck="name"):
            frappe.delete_doc(doctype, docname, ignore_permissions=True, force=True)

    for doctype in ("Warehouse", "Cost Center", "Account"):
        docs = frappe.get_all(
            doctype,
            filters={"company": company},
            fields=["name"],
            order_by="lft desc, creation desc",
        )
        for doc in docs:
            frappe.delete_doc(doctype, doc.name, ignore_permissions=True, force=True)

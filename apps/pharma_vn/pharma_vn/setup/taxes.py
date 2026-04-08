import frappe


VAT_RATE_OPTIONS = ("0", "5", "8", "10")
SALES_DIRECTION = "sales"
PURCHASE_DIRECTION = "purchase"


def ensure_vietnam_tax_setup():
    _ensure_accounts_settings()

    for company in frappe.get_all("Company", pluck="name"):
        _ensure_item_tax_templates(company)


def get_vat_rate_options():
    return "\n" + "\n".join(VAT_RATE_OPTIONS)


def resolve_item_tax_template_name(*, company, direction, vat_rate):
    rate = normalize_vat_rate(vat_rate)
    if rate == 0:
        return None

    company_abbr = frappe.get_cached_value("Company", company, "abbr")
    direction_label = "Sales" if direction == SALES_DIRECTION else "Purchase"
    template_title = f"VAT {rate}% {direction_label} Item - {company_abbr}"
    return frappe.db.get_value(
        "Item Tax Template",
        {"title": template_title, "company": company},
        "name",
    )


def normalize_vat_rate(value):
    if value in (None, ""):
        return 0

    rate = int(float(value))
    if str(rate) not in VAT_RATE_OPTIONS:
        frappe.throw(f"Unsupported VAT rate: {value}")
    return rate


def _ensure_accounts_settings():
    settings = frappe.get_single("Accounts Settings")
    changed = False

    if not settings.add_taxes_from_item_tax_template:
        settings.add_taxes_from_item_tax_template = 1
        changed = True

    if settings.add_taxes_from_taxes_and_charges_template:
        settings.add_taxes_from_taxes_and_charges_template = 0
        changed = True

    if changed:
        settings.save(ignore_permissions=True)


def _ensure_item_tax_templates(company):
    company_abbr = frappe.get_cached_value("Company", company, "abbr")

    for rate in (5, 8, 10):
        _ensure_item_tax_template(
            company=company,
            company_abbr=company_abbr,
            direction=SALES_DIRECTION,
            rate=rate,
            account_number=f"3331{rate}",
            account_name=f"VAT Output {rate}%",
            root_type="Liability",
        )
        _ensure_item_tax_template(
            company=company,
            company_abbr=company_abbr,
            direction=PURCHASE_DIRECTION,
            rate=rate,
            account_number=f"1331{rate}",
            account_name=f"VAT Input {rate}%",
            root_type="Asset",
        )


def _ensure_item_tax_template(*, company, company_abbr, direction, rate, account_number, account_name, root_type):
    direction_label = "Sales" if direction == SALES_DIRECTION else "Purchase"
    template_title = f"VAT {rate}% {direction_label} Item - {company_abbr}"
    account_head = _ensure_tax_account(
        company=company,
        account_number=account_number,
        account_name=account_name,
        root_type=root_type,
    )

    template_name = frappe.db.get_value(
        "Item Tax Template",
        {"title": template_title, "company": company},
        "name",
    )
    if template_name:
        doc = frappe.get_doc("Item Tax Template", template_name)
        if doc.company != company:
            doc.company = company
        if not doc.taxes or doc.taxes[0].tax_type != account_head or float(doc.taxes[0].tax_rate or 0) != rate:
            doc.set("taxes", [{"tax_type": account_head, "tax_rate": rate}])
        doc.disabled = 0
        doc.save(ignore_permissions=True)
        return

    frappe.get_doc(
        {
            "doctype": "Item Tax Template",
            "title": template_title,
            "company": company,
            "disabled": 0,
            "taxes": [{"tax_type": account_head, "tax_rate": rate}],
        }
    ).insert(ignore_permissions=True)


def _ensure_tax_account(*, company, account_number, account_name, root_type):
    company_abbr = frappe.get_cached_value("Company", company, "abbr")
    account_head = f"{account_number} - {account_name} - {company_abbr}"

    if frappe.db.exists("Account", account_head):
        return account_head

    parent_account = frappe.db.get_value(
        "Account",
        {
            "company": company,
            "root_type": root_type,
            "is_group": 1,
            "account_name": "Duties and Taxes" if root_type == "Liability" else "Current Assets",
        },
        "name",
    )
    if not parent_account:
        parent_account = frappe.db.get_value(
            "Account",
            {"company": company, "root_type": root_type, "is_group": 1},
            "name",
            order_by="lft asc",
        )

    doc = frappe.get_doc(
        {
            "doctype": "Account",
            "account_name": account_name,
            "account_number": account_number,
            "company": company,
            "parent_account": parent_account,
            "root_type": root_type,
            "report_type": "Balance Sheet",
            "account_type": "Tax",
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name

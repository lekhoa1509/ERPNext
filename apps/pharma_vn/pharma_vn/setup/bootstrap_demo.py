import frappe
from frappe.utils import add_days, nowdate

from erpnext.setup.setup_wizard.operations.taxes_setup import make_taxes_and_charges_template
from erpnext.setup.setup_wizard.setup_wizard import setup_complete
from pharma_vn.customer_naming import CUSTOMER_NAMING_SERIES


BOOTSTRAP_ARGS = {
    "company_name": "Viet An Pharma JSC",
    "company_abbr": "VAP",
    "currency": "VND",
    "country": "Vietnam",
    "chart_of_accounts": "Standard with Numbers",
    "fy_start_date": "2026-01-01",
    "fy_end_date": "2026-12-31",
    "domain": "Manufacturing",
}

WAREHOUSE_GROUPS = [
    {"warehouse_name": "Raw Material", "parent_key": "root", "is_group": 1},
    {"warehouse_name": "Finished Goods", "parent_key": "root", "is_group": 1},
    {"warehouse_name": "Distribution Centers", "parent_key": "root", "is_group": 1},
    {"warehouse_name": "Quarantine", "parent_key": "Finished Goods", "is_group": 1},
    {"warehouse_name": "Released", "parent_key": "Finished Goods", "is_group": 1},
    {"warehouse_name": "HCM DC", "parent_key": "Distribution Centers", "is_group": 1},
    {"warehouse_name": "HN DC", "parent_key": "Distribution Centers", "is_group": 1},
]

WAREHOUSES = [
    {"warehouse_name": "RM Quarantine", "parent_key": "Raw Material"},
    {"warehouse_name": "RM Released", "parent_key": "Raw Material"},
    {"warehouse_name": "FG Quarantine", "parent_key": "Quarantine"},
    {"warehouse_name": "FG Released", "parent_key": "Released"},
    {"warehouse_name": "HCM Sellable", "parent_key": "HCM DC"},
    {"warehouse_name": "HN Sellable", "parent_key": "HN DC"},
]

ITEM_GROUPS = [
    {"item_group_name": "OTC Products", "parent_item_group": "Products"},
    {"item_group_name": "ETC Products", "parent_item_group": "Products"},
    {"item_group_name": "Supplements", "parent_item_group": "Products"},
]

ITEMS = [
    {
        "item_code": "PARA-500",
        "item_name": "Paracetamol 500mg",
        "item_group": "OTC Products",
        "valuation_rate": 1200,
        "standard_rate": 1800,
        "shelf_life_in_days": 720,
        "regulatory_category": "OTC",
        "drug_registration_no": "VD-12345-26",
        "storage_condition": "Store below 30C",
        "min_remaining_shelf_life_days": 365,
    },
    {
        "item_code": "AMOX-500",
        "item_name": "Amoxicillin 500mg",
        "item_group": "ETC Products",
        "valuation_rate": 2400,
        "standard_rate": 3300,
        "shelf_life_in_days": 540,
        "regulatory_category": "ETC",
        "drug_registration_no": "VD-22345-26",
        "storage_condition": "Store below 25C",
        "min_remaining_shelf_life_days": 365,
    },
    {
        "item_code": "VITC-1000",
        "item_name": "Vitamin C 1000mg",
        "item_group": "Supplements",
        "valuation_rate": 1800,
        "standard_rate": 2600,
        "shelf_life_in_days": 365,
        "regulatory_category": "Supplement",
        "drug_registration_no": "TPCN-1026",
        "storage_condition": "Store in dry place",
        "min_remaining_shelf_life_days": 270,
    },
]

CUSTOMERS = [
    {
        "customer_name": "Nha Thuoc An Khang",
        "customer_group": "Commercial",
        "territory": "Vietnam",
        "customer_channel": "Pharmacy",
        "license_no": "NT-001-HCM",
        "sales_region": "South",
        "credit_review_status": "Approved",
        "credit_limit": 30000000,
        "contact_name": "Duoc si Nguyen Lan",
        "contact_email": "nguyen.lan@ankhang.vn",
        "contact_phone": "02838228888",
        "billing_address": {
            "address_title": "Nha Thuoc An Khang",
            "address_line1": "128 Nguyen Dinh Chieu",
            "district": "Quan 3",
            "city": "Ho Chi Minh",
            "country": "Vietnam",
        },
        "shipping_address": {
            "address_title": "Nha Thuoc An Khang - Kho Giao",
            "address_line1": "39 Le Van Sy",
            "district": "Tan Binh",
            "city": "Ho Chi Minh",
            "country": "Vietnam",
        },
    },
    {
        "customer_name": "Benh Vien Binh Dan",
        "customer_group": "Government",
        "territory": "Vietnam",
        "customer_channel": "Hospital",
        "license_no": "BV-002-HCM",
        "sales_region": "South",
        "credit_review_status": "Approved",
        "credit_limit": 150000000,
        "contact_name": "Phong Vat tu Y te",
        "contact_email": "mua.sam@binhdan.vn",
        "contact_phone": "02838394747",
        "billing_address": {
            "address_title": "Benh Vien Binh Dan",
            "address_line1": "371 Dien Bien Phu",
            "district": "Quan 3",
            "city": "Ho Chi Minh",
            "country": "Vietnam",
        },
        "shipping_address": {
            "address_title": "Benh Vien Binh Dan - Kho Duoc",
            "address_line1": "408 Dien Bien Phu",
            "district": "Quan 3",
            "city": "Ho Chi Minh",
            "country": "Vietnam",
        },
    },
]

SUPPLIERS = [
    {
        "supplier_name": "Duoc Lieu Mekong",
        "supplier_group": "Raw Material",
        "supplier_type": "Company",
        "gmp_certificate_no": "GMP-RM-2026-01",
        "approved_vendor_status": "Approved",
    },
    {
        "supplier_name": "Bao Bi Sai Gon",
        "supplier_group": "Pharmaceutical",
        "supplier_type": "Company",
        "gmp_certificate_no": "GMP-PM-2026-02",
        "approved_vendor_status": "Approved",
    },
]

BATCHES = [
    {"batch_id": "PARA500-2601-001", "item": "PARA-500", "days_to_expiry": 720},
    {"batch_id": "AMOX500-2601-001", "item": "AMOX-500", "days_to_expiry": 540},
    {"batch_id": "VITC1000-2601-001", "item": "VITC-1000", "days_to_expiry": 365},
]

MODES_OF_PAYMENT = [
    "Bank Transfer",
    "Cash",
]

SAMPLE_SALES_ORDERS = [
    {
        "customer": "Benh Vien Binh Dan",
        "items": [
            {"item_code": "AMOX-500", "qty": 1200, "warehouse_name": "FG Released"},
            {"item_code": "PARA-500", "qty": 2000, "warehouse_name": "FG Released"},
        ],
        "po_no": "PO-BVBD-2026-0017",
        "po_date": "2026-04-06",
        "description": "Don hang ETC giao dot 1 thang 04/2026",
        "requested_date": "2026-04-08",
        "payment_method": "Bank Transfer",
        "payment_reference_type": "Contract",
        "distribution_channel": "Hospital",
        "delivery_priority": "High",
        "send_order_confirmation": 1,
        "shipping_condition": "Ambient",
        "workflow_state": "In Preparation",
    }
]

SAMPLE_STOCK_RECEIPTS = [
    {
        "reference_no": "BOOTSTRAP-STOCK-2026-0001",
        "supplier": "Duoc Lieu Mekong",
        "warehouse_name": "FG Released",
        "items": [
            {"item_code": "PARA-500", "qty": 5000, "batch_no": "PARA500-2601-001", "rate": 1200},
            {"item_code": "AMOX-500", "qty": 3000, "batch_no": "AMOX500-2601-001", "rate": 2400},
        ],
    }
]


def bootstrap_vietnam_demo():
    company = _resolve_or_create_company()
    _ensure_vietnamese_language()
    _ensure_item_groups()
    _ensure_warehouses(company)
    _ensure_tax_templates(company)
    _ensure_modes_of_payment()
    _ensure_customers()
    _ensure_suppliers()
    _ensure_items()
    _ensure_item_prices()
    _ensure_batches()
    _set_pharma_defaults(company)
    _ensure_sample_stock(company)
    _ensure_sample_sales_orders(company)
    frappe.db.commit()


def _resolve_or_create_company():
    default_company = frappe.db.get_single_value("Global Defaults", "default_company")
    if default_company and frappe.db.exists("Company", default_company):
        return default_company

    company_name = BOOTSTRAP_ARGS["company_name"]
    if not frappe.db.exists("Company", company_name):
        setup_complete(frappe._dict(BOOTSTRAP_ARGS))
    return company_name


def _ensure_item_groups():
    for row in ITEM_GROUPS:
        if frappe.db.exists("Item Group", row["item_group_name"]):
            continue

        frappe.get_doc(
            {
                "doctype": "Item Group",
                "item_group_name": row["item_group_name"],
                "parent_item_group": row["parent_item_group"],
                "is_group": 0,
            }
        ).insert(ignore_permissions=True)


def _ensure_vietnamese_language():
    language_code = "vi"
    language_name = "Tiếng Việt"

    if frappe.db.exists("Language", language_code):
        frappe.db.set_value("Language", language_code, "enabled", 1, update_modified=False)
        existing_name = frappe.db.get_value("Language", language_code, "language_name")
        if not existing_name:
            frappe.db.set_value(
                "Language",
                language_code,
                "language_name",
                language_name,
                update_modified=False,
            )
        return

    frappe.get_doc(
        {
            "doctype": "Language",
            "language_code": language_code,
            "language_name": language_name,
            "enabled": 1,
        }
    ).insert(ignore_permissions=True)


def _ensure_warehouses(company):
    root_warehouse = _get_root_warehouse(company)
    warehouse_map = {"root": root_warehouse}

    for row in WAREHOUSE_GROUPS:
        parent_name = warehouse_map[row["parent_key"]]
        warehouse_map[row["warehouse_name"]] = _ensure_warehouse(
            warehouse_name=row["warehouse_name"],
            company=company,
            parent_warehouse=parent_name,
            is_group=row["is_group"],
        )

    for row in WAREHOUSES:
        _ensure_warehouse(
            warehouse_name=row["warehouse_name"],
            company=company,
            parent_warehouse=warehouse_map[row["parent_key"]],
            is_group=0,
        )


def _ensure_tax_templates(company):
    _delete_template_if_exists("Sales Taxes and Charges Template", company, "Vietnam Tax")
    _delete_template_if_exists("Purchase Taxes and Charges Template", company, "Vietnam Tax")

    for rate in (5.0, 8.0, 10.0):
        make_taxes_and_charges_template(
            company,
            "Sales Taxes and Charges Template",
            {
                "title": f"VAT {int(rate)}% Sales",
                "is_default": 1 if rate == 10.0 else 0,
                "taxes": [
                    {
                        "account_head": {
                            "account_name": f"VAT Output {int(rate)}%",
                            "account_number": f"3331{int(rate)}",
                            "tax_rate": rate,
                            "root_type": "Liability",
                        }
                    }
                ],
            },
        )
        make_taxes_and_charges_template(
            company,
            "Purchase Taxes and Charges Template",
            {
                "title": f"VAT {int(rate)}% Purchase",
                "is_default": 1 if rate == 10.0 else 0,
                "taxes": [
                    {
                        "account_head": {
                            "account_name": f"VAT Input {int(rate)}%",
                            "account_number": f"1331{int(rate)}",
                            "tax_rate": rate,
                            "root_type": "Asset",
                        }
                    }
                ],
            },
        )


def _ensure_customers():
    for row in CUSTOMERS:
        customer_name = row["customer_name"]
        customer_docname = _get_customer_docname(customer_name)
        if not customer_docname:
            customer_doc = frappe.get_doc(
                {
                    "doctype": "Customer",
                    "customer_name": customer_name,
                    "customer_type": "Company",
                    "customer_group": row["customer_group"],
                    "territory": row["territory"],
                    "naming_series": CUSTOMER_NAMING_SERIES,
                    "customer_channel": row["customer_channel"],
                    "license_no": row["license_no"],
                    "sales_region": row["sales_region"],
                    "credit_review_status": row["credit_review_status"],
                }
            ).insert(ignore_permissions=True)
            customer_docname = customer_doc.name

        _ensure_customer_contact(row, customer_docname)
        _ensure_customer_addresses(row, customer_docname)
        _ensure_customer_credit_limit(customer_docname, row.get("credit_limit"))


def _ensure_suppliers():
    for row in SUPPLIERS:
        if frappe.db.exists("Supplier", row["supplier_name"]):
            continue

        frappe.get_doc(
            {
                "doctype": "Supplier",
                "supplier_name": row["supplier_name"],
                "supplier_group": row["supplier_group"],
                "supplier_type": row["supplier_type"],
                "gmp_certificate_no": row["gmp_certificate_no"],
                "approved_vendor_status": row["approved_vendor_status"],
            }
        ).insert(ignore_permissions=True)


def _ensure_items():
    for row in ITEMS:
        item_values = {
            "item_name": row["item_name"],
            "item_group": row["item_group"],
            "stock_uom": "Nos",
            "is_stock_item": 1,
            "include_item_in_manufacturing": 1,
            "has_batch_no": 1,
            "create_new_batch": 1,
            "batch_number_series": f"BATCH-{row['item_code']}-.#####",
            "has_expiry_date": 1,
            "shelf_life_in_days": row["shelf_life_in_days"],
            "valuation_rate": row["valuation_rate"],
            "standard_rate": row["standard_rate"],
            "regulatory_category": row["regulatory_category"],
            "drug_registration_no": row["drug_registration_no"],
            "storage_condition": row["storage_condition"],
            "qa_required": 1,
            "min_remaining_shelf_life_days": row["min_remaining_shelf_life_days"],
            "pharma_default_sales_vat_rate": "10",
            "pharma_default_purchase_vat_rate": "10",
        }

        if frappe.db.exists("Item", row["item_code"]):
            frappe.db.set_value("Item", row["item_code"], item_values, update_modified=False)
            continue

        frappe.get_doc(
            {
                "doctype": "Item",
                "item_code": row["item_code"],
                **item_values,
            }
        ).insert(ignore_permissions=True)


def _ensure_item_prices():
    for row in ITEMS:
        for price_list, rate in (
            ("Standard Buying", row["valuation_rate"]),
            ("Standard Selling", row["standard_rate"]),
        ):
            if frappe.db.exists(
                "Item Price",
                {"item_code": row["item_code"], "price_list": price_list, "currency": "VND"},
            ):
                continue

            frappe.get_doc(
                {
                    "doctype": "Item Price",
                    "item_code": row["item_code"],
                    "price_list": price_list,
                    "currency": "VND",
                    "price_list_rate": rate,
                }
            ).insert(ignore_permissions=True)


def _ensure_batches():
    today = nowdate()
    for row in BATCHES:
        if frappe.db.exists("Batch", row["batch_id"]):
            continue

        frappe.get_doc(
            {
                "doctype": "Batch",
                "batch_id": row["batch_id"],
                "item": row["item"],
                "manufacturing_date": today,
                "expiry_date": add_days(today, row["days_to_expiry"]),
                "batch_status": "Released",
            }
        ).insert(ignore_permissions=True)


def _ensure_modes_of_payment():
    for mode in MODES_OF_PAYMENT:
        if frappe.db.exists("Mode of Payment", mode):
            continue

        frappe.get_doc(
            {
                "doctype": "Mode of Payment",
                "mode_of_payment": mode,
                "type": "Bank" if mode == "Bank Transfer" else "Cash",
            }
        ).insert(ignore_permissions=True)


def _get_customer_docname(customer_reference):
    if not customer_reference:
        return ""
    if frappe.db.exists("Customer", customer_reference):
        return customer_reference
    return frappe.db.get_value("Customer", {"customer_name": customer_reference}, "name") or ""


def _ensure_customer_contact(row, customer_docname):
    customer_name = row["customer_name"]
    contact_name = row.get("contact_name")
    if not contact_name:
        return

    existing = frappe.db.get_value("Contact", {"first_name": contact_name}, "name")
    if existing:
        contact = frappe.get_doc("Contact", existing)
    else:
        contact = frappe.get_doc(
            {
                "doctype": "Contact",
                "first_name": contact_name,
                "is_primary_contact": 1,
                "links": [
                    {
                        "link_doctype": "Customer",
                        "link_name": customer_docname,
                    }
                ],
            }
        ).insert(ignore_permissions=True)

    if row.get("contact_email") and not contact.get("email_ids"):
        contact.append(
            "email_ids",
            {
                "email_id": row["contact_email"],
                "is_primary": 1,
            },
        )
    if row.get("contact_phone") and not contact.get("phone_nos"):
        contact.append(
            "phone_nos",
            {
                "phone": row["contact_phone"],
                "is_primary_phone": 1,
            },
        )
    contact.save(ignore_permissions=True)

    frappe.db.set_value("Customer", customer_docname, "customer_primary_contact", contact.name, update_modified=False)


def _ensure_customer_addresses(row, customer_docname):
    billing_address = _ensure_address(customer_docname, row.get("billing_address"), is_shipping_address=0)
    shipping_address = _ensure_address(customer_docname, row.get("shipping_address"), is_shipping_address=1)

    if billing_address:
        frappe.db.set_value(
            "Customer",
            customer_docname,
            "customer_primary_address",
            billing_address,
            update_modified=False,
        )
    if shipping_address and frappe.db.has_column("Customer", "shipping_address_name"):
        frappe.db.set_value(
            "Customer",
            customer_docname,
            "shipping_address_name",
            shipping_address,
            update_modified=False,
        )


def _ensure_address(customer_docname, address_data, is_shipping_address):
    if not address_data:
        return None

    address_title = address_data["address_title"]
    existing = frappe.db.get_value("Address", {"address_title": address_title}, "name")
    if existing:
        return existing

    address = frappe.get_doc(
        {
            "doctype": "Address",
            "address_title": address_title,
            "address_type": "Shipping" if is_shipping_address else "Billing",
            "address_line1": address_data["address_line1"],
            "address_line2": address_data.get("district"),
            "city": address_data["city"],
            "country": address_data["country"],
            "links": [
                {
                    "link_doctype": "Customer",
                    "link_name": customer_docname,
                }
            ],
        }
    ).insert(ignore_permissions=True)
    return address.name


def _ensure_customer_credit_limit(customer_docname, credit_limit):
    if credit_limit is None or not frappe.db.table_exists("Customer Credit Limit"):
        return

    existing = frappe.db.get_value(
        "Customer Credit Limit",
        {"parent": customer_docname, "company": BOOTSTRAP_ARGS["company_name"]},
        "name",
    )
    if existing:
        frappe.db.set_value("Customer Credit Limit", existing, "credit_limit", credit_limit, update_modified=False)
        return

    customer = frappe.get_doc("Customer", customer_docname)
    customer.append(
        "credit_limits",
        {
            "company": BOOTSTRAP_ARGS["company_name"],
            "credit_limit": credit_limit,
        },
    )
    customer.save(ignore_permissions=True)


def _ensure_sample_sales_orders(company):
    for row in SAMPLE_SALES_ORDERS:
        customer_docname = _get_customer_docname(row["customer"]) or row["customer"]
        existing_order = frappe.db.get_value("Sales Order", {"po_no": row["po_no"], "customer": customer_docname}, "name")
        order = frappe.get_doc("Sales Order", existing_order) if existing_order else frappe.new_doc("Sales Order")
        order.company = company
        order.customer = customer_docname
        order.transaction_date = row["po_date"]
        order.delivery_date = row["requested_date"]
        order.po_no = row["po_no"]
        order.po_date = row["po_date"]
        order.taxes_and_charges = "VAT 10% Sales - VAP"
        order.pharma_order_description = row["description"]
        order.pharma_requested_date = row["requested_date"]
        order.pharma_issue_date = row["po_date"]
        order.pharma_payment_method = row["payment_method"]
        order.pharma_payment_reference_type = row["payment_reference_type"]
        order.pharma_distribution_channel = row["distribution_channel"]
        order.pharma_delivery_priority = row["delivery_priority"]
        order.pharma_send_order_confirmation = row["send_order_confirmation"]
        order.pharma_shipping_condition = row["shipping_condition"]
        order.workflow_state = row["workflow_state"]
        order.set("items", [])

        customer = frappe.get_cached_doc("Customer", customer_docname)
        if customer.customer_primary_contact:
            order.contact_person = customer.customer_primary_contact
        if customer.customer_primary_address:
            order.customer_address = customer.customer_primary_address

        shipping_address = frappe.db.get_value(
            "Dynamic Link",
            {
                "link_doctype": "Customer",
                "link_name": customer_docname,
                "parenttype": "Address",
            },
            "parent",
            order_by="creation desc",
        )
        if shipping_address:
            order.shipping_address_name = shipping_address

        for item_row in row["items"]:
            warehouse = frappe.db.get_value(
                "Warehouse",
                {"warehouse_name": item_row["warehouse_name"], "company": company},
                "name",
            )
            order.append(
                "items",
                {
                    "item_code": item_row["item_code"],
                    "qty": item_row["qty"],
                    "warehouse": warehouse,
                    "delivery_date": row["requested_date"],
                },
            )

        order.flags.ignore_permissions = True
        order.set_missing_values()
        order.calculate_taxes_and_totals()
        if existing_order:
            order.save(ignore_permissions=True)
        else:
            order.insert(ignore_permissions=True)


def _set_pharma_defaults(company):
    default_time_zone = "Asia/Ho_Chi_Minh"
    default_country = "Vietnam"
    default_currency = "VND"
    default_language = "en"
    company_abbr = frappe.db.get_value("Company", company, "abbr")
    released_warehouse = frappe.db.get_value(
        "Warehouse",
        {"warehouse_name": "FG Released", "company": company},
        "name",
    )

    frappe.db.set_single_value("Global Defaults", "default_company", company)
    frappe.db.set_single_value("System Settings", "setup_complete", 1)
    frappe.db.set_single_value("System Settings", "enable_scheduler", 1)
    frappe.db.set_single_value("System Settings", "country", default_country)
    frappe.db.set_single_value("System Settings", "currency", default_currency)
    frappe.db.set_single_value("System Settings", "language", default_language)
    frappe.db.set_single_value("System Settings", "time_zone", default_time_zone)
    frappe.db.set_default("setup_complete", 1)
    frappe.db.set_default("enable_scheduler", 1)
    frappe.db.set_default("desktop:home_page", "workspace")
    frappe.db.set_default("country", default_country)
    frappe.db.set_default("currency", default_currency)
    frappe.db.set_default("enable_serial_and_batch_no_for_item", 1)
    frappe.db.set_default("lang", default_language)
    frappe.db.set_default("time_zone", default_time_zone)
    for user_default_parent in ("Administrator", "Guest"):
        frappe.db.set_default("enable_serial_and_batch_no_for_item", 1, parent=user_default_parent)
        frappe.db.set_default("time_zone", default_time_zone, parent=user_default_parent)
        frappe.db.set_default("lang", default_language, parent=user_default_parent)
    for app in frappe.get_all("Installed Application", pluck="name"):
        frappe.db.set_value("Installed Application", app, "is_setup_complete", 1, update_modified=False)
    if released_warehouse:
        frappe.db.set_single_value("Stock Settings", "default_warehouse", released_warehouse)
    frappe.db.set_single_value("Stock Settings", "enable_serial_and_batch_no_for_item", 1)
    frappe.db.set_single_value("Stock Settings", "use_serial_batch_fields", 1)
    frappe.db.set_single_value("Stock Settings", "auto_create_serial_and_batch_bundle_for_outward", 1)

    if company_abbr:
        frappe.db.set_value("Company", company, "default_currency", default_currency)

    if frappe.db.has_column("User", "default_workspace"):
        frappe.db.set_value("User", "Administrator", "default_workspace", "Home", update_modified=False)
    if frappe.db.has_column("User", "language"):
        frappe.db.set_value("User", "Administrator", "language", default_language, update_modified=False)
    if frappe.db.has_column("User", "time_zone"):
        frappe.db.set_value(
            "User",
            "Administrator",
            "time_zone",
            default_time_zone,
            update_modified=False,
        )


def _ensure_sample_stock(company):
    for row in SAMPLE_STOCK_RECEIPTS:
        existing = frappe.db.get_value(
            "Purchase Receipt",
            {"supplier_delivery_note": row["reference_no"], "supplier": row["supplier"]},
            "name",
        )
        if existing:
            continue

        warehouse = frappe.db.get_value(
            "Warehouse",
            {"warehouse_name": row["warehouse_name"], "company": company},
            "name",
        )

        receipt = frappe.new_doc("Purchase Receipt")
        receipt.company = company
        receipt.supplier = row["supplier"]
        receipt.posting_date = nowdate()
        receipt.set_posting_time = 1
        receipt.posting_time = "08:00:00"
        receipt.supplier_delivery_note = row["reference_no"]
        receipt.set_warehouse = warehouse
        receipt.taxes_and_charges = "VAT 10% Purchase - VAP"

        for item_row in row["items"]:
            receipt.append(
                "items",
                {
                    "item_code": item_row["item_code"],
                    "qty": item_row["qty"],
                    "warehouse": warehouse,
                    "rate": item_row["rate"],
                    "use_serial_batch_fields": 1,
                    "batch_no": item_row["batch_no"],
                },
            )

        receipt.flags.ignore_permissions = True
        receipt.set_missing_values()
        receipt.calculate_taxes_and_totals()
        receipt.insert(ignore_permissions=True)
        receipt.submit()


def _get_root_warehouse(company):
    warehouses = frappe.get_all(
        "Warehouse",
        filters={"company": company, "is_group": 1},
        fields=["name", "parent_warehouse"],
        order_by="creation asc",
    )
    for warehouse in warehouses:
        if not warehouse.parent_warehouse:
            return warehouse.name
    frappe.throw(f"Could not determine root warehouse for company {company}")


def _ensure_warehouse(warehouse_name, company, parent_warehouse, is_group):
    existing = frappe.db.get_value(
        "Warehouse",
        {"warehouse_name": warehouse_name, "company": company},
        "name",
    )
    if existing:
        return existing

    warehouse = frappe.get_doc(
        {
            "doctype": "Warehouse",
            "warehouse_name": warehouse_name,
            "company": company,
            "parent_warehouse": parent_warehouse,
            "is_group": is_group,
        }
    ).insert(ignore_permissions=True)
    return warehouse.name


def _delete_template_if_exists(doctype, company, title):
    template_name = frappe.db.get_value(doctype, {"company": company, "title": title}, "name")
    if template_name:
        frappe.delete_doc(doctype, template_name, ignore_permissions=True, force=True)

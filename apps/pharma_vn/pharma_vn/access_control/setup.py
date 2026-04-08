import frappe


DEFAULT_FUNCTIONS = [
    ("ACC_DASHBOARD", "Accounting Dashboard", "Finance", "View accounting dashboard and summaries"),
    ("ACC_PAYMENT_ENTRY", "Payment Entry", "Finance", "Create and manage payment entries"),
    ("ACC_JOURNAL_ENTRY", "Journal Entry", "Finance", "Create and manage journal entries"),
    ("ACC_AR_AP", "AR / AP Operations", "Finance", "Work with receivables and payables operations"),
    ("WH_PURCHASE_RECEIPT", "Purchase Receipt", "Warehouse", "Receive stock into warehouse"),
    ("WH_DELIVERY_NOTE", "Delivery Note", "Warehouse", "Deliver stock from warehouse"),
    ("WH_STOCK_ENTRY", "Stock Entry", "Warehouse", "Perform stock movement and adjustments"),
    ("WH_WAREHOUSE_OVERVIEW", "Warehouse Overview", "Warehouse", "View stock and warehouse operations"),
]

DEFAULT_GROUPS = [
    {
        "name": "Accountant Base",
        "description": "Base access set for accounting staff.",
        "permissions_matrix": [
            ("ACC_DASHBOARD", "Allow"),
            ("ACC_PAYMENT_ENTRY", "Allow"),
            ("ACC_JOURNAL_ENTRY", "Allow"),
            ("ACC_AR_AP", "Allow"),
        ],
    }
]


def after_migrate():
    ensure_access_control_defaults()


def ensure_access_control_defaults():
    ensure_function_catalog()
    ensure_default_groups()


def ensure_function_catalog():
    for name, label, module, description in DEFAULT_FUNCTIONS:
        if frappe.db.exists("Function Access", name):
            continue
        frappe.get_doc(
            {
                "doctype": "Function Access",
                "function_code": name,
                "label": label,
                "module_area": module,
                "description": description,
                "is_active": 1,
            }
        ).insert(ignore_permissions=True)


def ensure_default_groups():
    for group in DEFAULT_GROUPS:
        if frappe.db.exists("Access Group", group["name"]):
            continue
        doc = frappe.get_doc(
            {
                "doctype": "Access Group",
                "group_name": group["name"],
                "description": group["description"],
                "permissions_matrix": [
                    {"function_access": code, "access_mode": mode}
                    for code, mode in group["permissions_matrix"]
                ],
            }
        )
        doc.insert(ignore_permissions=True)

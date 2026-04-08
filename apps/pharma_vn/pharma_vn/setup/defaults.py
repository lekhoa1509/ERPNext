import frappe


DEFAULTS = {
    "pharma_default_shelf_life_days": "180",
    "pharma_near_expiry_alert_days": "180",
    "pharma_alert_role_primary": "QA Manager",
    "pharma_alert_role_secondary": "Warehouse Manager",
}


def create_default_settings():
    for key, value in DEFAULTS.items():
        if not frappe.db.get_default(key):
            frappe.db.set_default(key, value)


import frappe


def disable_sales_order_workflow():
    for workflow_name in frappe.get_all(
        "Workflow",
        filters={"document_type": "Sales Order"},
        pluck="name",
    ):
        frappe.db.set_value("Workflow", workflow_name, "is_active", 0, update_modified=False)

    frappe.db.commit()

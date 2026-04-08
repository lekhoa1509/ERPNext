import frappe

from pharma_vn.access_control.service import resolve_user_access


@frappe.whitelist()
def get_user_access_resolution(user):
    return {"data": resolve_user_access(user)}

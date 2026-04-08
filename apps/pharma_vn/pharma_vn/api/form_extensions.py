import frappe

from pharma_vn.dynamic_forms.extension_service import build_base_schema, get_target_field_options


@frappe.whitelist()
def get_target_fields(target_doctype):
    return {
        "data": get_target_field_options(target_doctype),
        "schema": build_base_schema(target_doctype),
    }

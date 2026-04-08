import frappe
from frappe import _
from frappe.model.document import Document

from pharma_vn.dynamic_forms.extension_service import (
    apply_extension,
    disable_extension,
    refresh_reference_json,
    uninstall_extension,
)


class FormExtensionManager(Document):
    def validate(self):
        if not self.status:
            self.status = "Draft"
        refresh_reference_json(self)

    @frappe.whitelist()
    def apply_extension(self):
        if not self.extension_fields:
            frappe.throw(_("Add at least one extension field before applying"))
        return apply_extension(self)

    @frappe.whitelist()
    def disable_extension(self):
        return disable_extension(self)

    @frappe.whitelist()
    def uninstall_extension(self):
        return uninstall_extension(self)

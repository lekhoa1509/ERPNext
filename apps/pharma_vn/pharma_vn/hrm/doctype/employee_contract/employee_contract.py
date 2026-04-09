import frappe
from frappe.model.document import Document


class EmployeeContract(Document):
    def validate(self):
        self._ensure_single_active_contract()

    def _ensure_single_active_contract(self):
        if self.status != "Active" or not self.employee:
            return

        filters = {
            "employee": self.employee,
            "status": "Active",
            "docstatus": ("!=", 2),
            "name": ("!=", self.name),
        }
        if frappe.db.exists("Employee Contract", filters):
            frappe.throw("Nhân sự này đã có một hợp đồng đang hiệu lực.")

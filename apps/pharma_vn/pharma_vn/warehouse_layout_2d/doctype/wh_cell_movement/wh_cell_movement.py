import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class WHCellMovement(Document):
    def validate(self):
        if not flt(self.qty_change):
            frappe.throw(_("Qty Change cannot be 0"))

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint

from pharma_vn.warehouse_layout_2d.service import sync_layout_cells


class WHLayout(Document):
    def validate(self):
        self.total_rows = cint(self.total_rows)
        self.total_columns = cint(self.total_columns)

        if self.total_rows <= 0:
            frappe.throw(_("Total Rows must be greater than 0"))

        if self.total_columns <= 0:
            frappe.throw(_("Total Columns must be greater than 0"))

        if self.warehouse and not self.company:
            self.company = frappe.db.get_value("Warehouse", self.warehouse, "company")

    def on_update(self):
        if self.auto_generate_cells:
            sync_layout_cells(self)

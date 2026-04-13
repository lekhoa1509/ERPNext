import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint

from pharma_vn.warehouse_layout_2d.service import get_layout_dimensions, sync_layout_cells


class WHLayout(Document):
    def validate(self):
        dimensions = get_layout_dimensions(self)
        self.total_floors = dimensions["total_floors"]
        self.total_rails = dimensions["total_rails"]
        self.total_blocks = dimensions["total_blocks"]
        self.total_depths = dimensions["total_depths"]

        if self.total_floors <= 0:
            frappe.throw(_("Total Floors must be greater than 0"))

        if self.total_rails <= 0:
            frappe.throw(_("Total Rails must be greater than 0"))

        if self.total_blocks <= 0:
            frappe.throw(_("Total Blocks must be greater than 0"))

        if self.total_depths <= 0:
            frappe.throw(_("Total Depths must be greater than 0"))

        if self.warehouse and not self.company:
            self.company = frappe.db.get_value("Warehouse", self.warehouse, "company")

    def on_update(self):
        if self.auto_generate_cells:
            sync_layout_cells(self)

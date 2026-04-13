import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint

from pharma_vn.warehouse_layout_2d.service import build_cell_code, build_cell_label


class WHCell(Document):
    def validate(self):
        self.floor = cint(self.floor)
        self.rail = cint(self.rail)
        self.block = cint(self.block)
        self.depth = cint(self.depth)

        if self.floor <= 0:
            frappe.throw(_("Floor must be greater than 0"))

        if self.rail <= 0:
            frappe.throw(_("Rail must be greater than 0"))

        if self.block <= 0:
            frappe.throw(_("Block must be greater than 0"))

        if self.depth <= 0:
            frappe.throw(_("Depth must be greater than 0"))

        if self.layout:
            layout = frappe.get_cached_value(
                "WH Layout",
                self.layout,
                ["warehouse", "total_floors", "total_rails", "total_blocks", "total_depths"],
                as_dict=True,
            )
            if layout:
                if layout.warehouse and not self.warehouse:
                    self.warehouse = layout.warehouse

                if cint(layout.total_floors) and self.floor > cint(layout.total_floors):
                    frappe.throw(_("Floor cannot exceed the configured layout"))

                if cint(layout.total_rails) and self.rail > cint(layout.total_rails):
                    frappe.throw(_("Rail cannot exceed the configured layout"))

                if cint(layout.total_blocks) and self.block > cint(layout.total_blocks):
                    frappe.throw(_("Block cannot exceed the configured layout"))

                if cint(layout.total_depths) and self.depth > cint(layout.total_depths):
                    frappe.throw(_("Depth cannot exceed the configured layout"))

        self.cell_code = self.cell_code or build_cell_code(self.floor, self.rail, self.block, self.depth)
        self.cell_label = self.cell_label or build_cell_label(self.floor, self.rail, self.block, self.depth)
        self.status = self.status or "Available"

        self._validate_uniqueness()

    def _validate_uniqueness(self):
        coordinate_filters = {
            "layout": self.layout,
            "floor": self.floor,
            "rail": self.rail,
            "block": self.block,
            "depth": self.depth,
            "name": ["!=", self.name or ""],
        }
        if frappe.db.exists("WH Cell", coordinate_filters):
            frappe.throw(_("Another cell already uses the same floor, rail, block, and depth in this layout"))

        code_filters = {
            "layout": self.layout,
            "cell_code": self.cell_code,
            "name": ["!=", self.name or ""],
        }
        if frappe.db.exists("WH Cell", code_filters):
            frappe.throw(_("Another cell already uses code {0} in this layout").format(self.cell_code))

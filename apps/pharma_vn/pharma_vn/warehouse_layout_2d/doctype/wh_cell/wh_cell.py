import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint

from pharma_vn.warehouse_layout_2d.service import build_cell_code, build_cell_label


class WHCell(Document):
    def validate(self):
        self.row_index = cint(self.row_index)
        self.column_index = cint(self.column_index)

        if self.row_index <= 0:
            frappe.throw(_("Row Index must be greater than 0"))

        if self.column_index <= 0:
            frappe.throw(_("Column Index must be greater than 0"))

        if self.layout:
            layout = frappe.get_cached_value(
                "WH Layout",
                self.layout,
                ["warehouse", "total_rows", "total_columns"],
                as_dict=True,
            )
            if layout:
                if layout.warehouse and not self.warehouse:
                    self.warehouse = layout.warehouse

                if cint(layout.total_rows) and self.row_index > cint(layout.total_rows):
                    frappe.throw(_("Row Index cannot exceed the layout grid"))

                if cint(layout.total_columns) and self.column_index > cint(layout.total_columns):
                    frappe.throw(_("Column Index cannot exceed the layout grid"))

        self.cell_code = self.cell_code or build_cell_code(self.row_index, self.column_index)
        self.cell_label = self.cell_label or build_cell_label(self.row_index, self.column_index)
        self.status = self.status or "Available"

        self._validate_uniqueness()

    def _validate_uniqueness(self):
        coordinate_filters = {
            "layout": self.layout,
            "row_index": self.row_index,
            "column_index": self.column_index,
            "name": ["!=", self.name or ""],
        }
        if frappe.db.exists("WH Cell", coordinate_filters):
            frappe.throw(_("Another cell already uses the same row and column in this layout"))

        code_filters = {
            "layout": self.layout,
            "cell_code": self.cell_code,
            "name": ["!=", self.name or ""],
        }
        if frappe.db.exists("WH Cell", code_filters):
            frappe.throw(_("Another cell already uses code {0} in this layout").format(self.cell_code))

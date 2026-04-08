import importlib
import unittest
from types import SimpleNamespace
from pathlib import Path
import sys

APP_ROOT = Path(__file__).resolve().parents[2]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from pharma_vn.tests.test_support import install_frappe_stub


class WarehouseLayoutServiceTest(unittest.TestCase):
    def setUp(self):
        frappe = install_frappe_stub()
        inserted_docs = []

        class FakeDoc(dict):
            def insert(self, ignore_permissions=False):
                inserted_docs.append(dict(self))
                return self

        frappe.get_doc = lambda values: FakeDoc(values)
        frappe.get_all = lambda *args, **kwargs: []
        frappe.db.set_value = lambda *args, **kwargs: None
        self.inserted_docs = inserted_docs
        self.module = importlib.reload(importlib.import_module("pharma_vn.warehouse_layout_2d.service"))

    def test_build_cell_code_uses_alpha_numeric_grid(self):
        self.assertEqual(self.module.build_cell_code(1, 3), "A3")
        self.assertEqual(self.module.build_cell_code(27, 2), "AA2")

    def test_sync_layout_cells_generates_missing_cells(self):
        layout_doc = SimpleNamespace(name="LAYOUT-1", warehouse="WH-A", total_rows=2, total_columns=2)
        self.module.sync_layout_cells(layout_doc)

        self.assertEqual(len(self.inserted_docs), 4)
        self.assertEqual(self.inserted_docs[0]["cell_code"], "A1")


if __name__ == "__main__":
    unittest.main()

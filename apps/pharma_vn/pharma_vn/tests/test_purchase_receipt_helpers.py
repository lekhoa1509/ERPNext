import importlib
import unittest
from pathlib import Path
import sys
from types import SimpleNamespace

APP_ROOT = Path(__file__).resolve().parents[2]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from pharma_vn.tests.test_support import install_frappe_stub


class PurchaseReceiptHelperTest(unittest.TestCase):
    def setUp(self):
        install_frappe_stub()
        self.module = importlib.reload(importlib.import_module("pharma_vn.automation.purchase_receipt"))

    def test_build_movement_remark_supports_inbound_and_reversal(self):
        inbound = self.module._build_movement_remark("PREC-0001", 2, is_reversal=False)
        reversal = self.module._build_movement_remark("PREC-0001", 2, is_reversal=True)

        self.assertIn("Inbound from Purchase Receipt PREC-0001, row 2.", inbound)
        self.assertIn("Reversed from Purchase Receipt PREC-0001, row 2.", reversal)

    def test_validate_storage_locations_handles_missing_custom_field_attributes(self):
        self.module._is_stock_item = lambda item_code: True
        self.module.warehouse_has_active_layout = lambda warehouse: False
        doc = SimpleNamespace(
            items=[
                SimpleNamespace(
                    idx=1,
                    item_code="FG-001",
                    warehouse="Stores - VP",
                )
            ]
        )

        self.module.validate_storage_locations(doc)

    def test_validate_storage_locations_backfills_layout_from_selected_cell(self):
        self.module._is_stock_item = lambda item_code: True
        self.module.warehouse_has_active_layout = lambda warehouse: False
        self.module.validate_cell_assignment = lambda *args, **kwargs: SimpleNamespace(layout="LAYOUT-A")
        row = SimpleNamespace(
            idx=1,
            item_code="FG-001",
            warehouse="Stores - VP",
            wh_cell="CELL-A1",
        )
        doc = SimpleNamespace(items=[row])

        self.module.validate_storage_locations(doc)

        self.assertEqual("LAYOUT-A", row.wh_layout)


if __name__ == "__main__":
    unittest.main()

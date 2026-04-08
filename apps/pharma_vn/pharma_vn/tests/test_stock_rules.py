import importlib
import unittest
from pathlib import Path
import sys

APP_ROOT = Path(__file__).resolve().parents[2]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from pharma_vn.tests.test_support import install_frappe_stub


class StockRuleTest(unittest.TestCase):
    def setUp(self):
        frappe = install_frappe_stub()
        batch_rows = {
            "B-OK": type(
                "Batch",
                (),
                {"expiry_date": "2026-05-01", "batch_status": "Released", "temperature_excursion_flag": 0},
            )(),
            "B-HOLD": type(
                "Batch",
                (),
                {"expiry_date": "2026-05-01", "batch_status": "Hold", "temperature_excursion_flag": 0},
            )(),
        }
        frappe.get_cached_value = lambda doctype, name, fields, as_dict=False: batch_rows.get(name)
        self.module = importlib.reload(importlib.import_module("pharma_vn.api.stock"))
        self.module.frappe.get_cached_value = lambda doctype, name, field, as_dict=False: (
            batch_rows.get(name) if doctype == "Batch" else 10
        )

    def test_released_batch_is_sellable(self):
        self.assertTrue(self.module._is_batch_sellable("B-OK", "2026-04-08", "ITEM-1"))

    def test_hold_batch_is_not_sellable(self):
        self.assertFalse(self.module._is_batch_sellable("B-HOLD", "2026-04-08", "ITEM-1"))


if __name__ == "__main__":
    unittest.main()

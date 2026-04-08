import unittest
from pathlib import Path
import sys

APP_ROOT = Path(__file__).resolve().parents[2]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from pharma_vn.services.alerts import detect_stock_mismatch_rows, make_alert_key


class AlertServiceTest(unittest.TestCase):
    def test_detect_stock_mismatch_rows_only_returns_differences(self):
        rows = [
            {"warehouse": "WH-A", "item_code": "ITEM-1", "cell_qty": 10, "bin_qty": 8},
            {"warehouse": "WH-B", "item_code": "ITEM-2", "cell_qty": 5, "bin_qty": 5},
        ]
        mismatches = detect_stock_mismatch_rows(rows)

        self.assertEqual(len(mismatches), 1)
        self.assertEqual(mismatches[0]["difference"], 2.0)

    def test_make_alert_key_is_stable(self):
        self.assertEqual(
            make_alert_key("invoice_fail", "SINV-0001", "Sales Invoice"),
            "invoice_fail|Sales Invoice|SINV-0001|-",
        )


if __name__ == "__main__":
    unittest.main()

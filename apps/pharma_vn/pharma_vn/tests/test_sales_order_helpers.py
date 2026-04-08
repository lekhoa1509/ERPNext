import importlib
import unittest
from pathlib import Path
import sys

APP_ROOT = Path(__file__).resolve().parents[2]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from pharma_vn.tests.test_support import install_frappe_stub


class SalesOrderHelperTest(unittest.TestCase):
    def setUp(self):
        install_frappe_stub()
        self.module = importlib.reload(importlib.import_module("pharma_vn.automation.sales_order"))

    def test_flt_or_none_handles_invalid_values(self):
        self.assertEqual(self.module.flt_or_none("12.5"), 12.5)
        self.assertIsNone(self.module.flt_or_none("not-a-number"))

    def test_resolve_credit_status_marks_order_over_limit(self):
        self.module._get_customer_credit_limit = lambda customer, company: 100
        self.module._get_customer_outstanding = lambda customer, company: 30
        doc = type("Doc", (), {"customer": "CUST-1", "company": "COMP", "grand_total": 80})()
        customer = type("Customer", (), {"credit_review_status": "Approved"})()

        status = self.module._resolve_credit_status(doc, customer=customer)
        self.assertEqual(status, "Over Limit")


if __name__ == "__main__":
    unittest.main()

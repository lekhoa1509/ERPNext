import importlib
import unittest
from pathlib import Path
import sys
from types import SimpleNamespace

APP_ROOT = Path(__file__).resolve().parents[2]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from pharma_vn.tests.test_support import install_frappe_stub


class CustomerNamingTest(unittest.TestCase):
    def setUp(self):
        install_frappe_stub()
        self.module = importlib.reload(importlib.import_module("pharma_vn.customer_naming"))

    def test_apply_customer_naming_generates_cm_series(self):
        called = []
        doc = SimpleNamespace(name="", naming_series="")

        generated = self.module.apply_customer_naming(
            doc,
            make_name=lambda pattern: called.append(pattern) or "CM-0007",
        )

        self.assertEqual(generated, "CM-0007")
        self.assertEqual(doc.name, "CM-0007")
        self.assertEqual(doc.naming_series, "CM-.####")
        self.assertEqual(called, ["CM-.####"])

    def test_apply_customer_naming_keeps_existing_series_name(self):
        doc = SimpleNamespace(name="CM-0042", naming_series="")

        generated = self.module.apply_customer_naming(doc, make_name=lambda pattern: "CM-9999")

        self.assertEqual(generated, "CM-0042")
        self.assertEqual(doc.name, "CM-0042")
        self.assertEqual(doc.naming_series, "CM-.####")

    def test_ensure_unique_customer_identity_blocks_duplicate_tax_id(self):
        self.frappe = importlib.import_module("frappe")
        self.frappe.db.has_column = lambda doctype, fieldname: fieldname in {"tax_id", "tax_code"}
        self.frappe.get_all = lambda doctype, filters=None, fields=None, limit_page_length=None: [
            {"name": "CM-0003", "customer_name": "Cong Ty Cu"},
        ] if filters and filters.get("tax_id") == "0319488060" else []

        with self.assertRaises(RuntimeError) as context:
            self.module.ensure_unique_customer_identity(
                SimpleNamespace(name="CM-0009", customer_name="Cong Ty Moi", tax_id="0319488060", tax_code="")
            )

        self.assertIn("Tax ID / MST 0319488060 already belongs to Customer Cong Ty Cu", str(context.exception))

    def test_ensure_unique_customer_identity_blocks_duplicate_customer_name(self):
        self.frappe = importlib.import_module("frappe")
        self.frappe.db.has_column = lambda doctype, fieldname: fieldname == "tax_id"

        def fake_get_all(doctype, filters=None, fields=None, limit_page_length=None):
            if filters and filters.get("customer_name") == "Cong Ty TNHH Vi Moc Viet":
                return [{"name": "CM-0004", "customer_name": "Cong Ty TNHH Vi Moc Viet"}]
            return []

        self.frappe.get_all = fake_get_all

        with self.assertRaises(RuntimeError) as context:
            self.module.ensure_unique_customer_identity(
                SimpleNamespace(
                    name="CM-0010",
                    customer_name="Cong Ty TNHH Vi Moc Viet",
                    tax_id="0319488061",
                )
            )

        self.assertIn(
            "Customer name Cong Ty TNHH Vi Moc Viet already exists as Cong Ty TNHH Vi Moc Viet",
            str(context.exception),
        )

import json
import unittest
from pathlib import Path
import sys
from types import SimpleNamespace

APP_ROOT = Path(__file__).resolve().parents[2]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from pharma_vn.tests.test_support import install_frappe_stub

install_frappe_stub()

from pharma_vn.dynamic_forms.service import build_schema, validate_submission


class DynamicFormServiceTest(unittest.TestCase):
    def test_build_schema_generates_fieldnames_and_keeps_layout_rows(self):
        doc = SimpleNamespace(
            name="Customer Intake",
            form_name="Customer Intake",
            is_published=1,
            allow_multiple_submissions=1,
            introduction="Collect intake data",
            success_message="Saved",
            fields_meta=[
                SimpleNamespace(
                    label="Customer Name",
                    fieldtype="Data",
                    fieldname="",
                    reqd=1,
                    options="",
                    link_doctype="",
                    default_value="",
                    placeholder="Acme",
                    description="",
                    width="Full",
                ),
                SimpleNamespace(
                    label="",
                    fieldtype="Section Break",
                    fieldname="",
                    reqd=0,
                    options="",
                    link_doctype="",
                    default_value="",
                    placeholder="",
                    description="",
                    width="Full",
                ),
            ],
        )

        schema = build_schema(doc)

        self.assertEqual(schema["fields"][0]["fieldname"], "customer_name")
        self.assertFalse(schema["fields"][0]["is_layout"])
        self.assertTrue(schema["fields"][1]["is_layout"])

    def test_validate_submission_coerces_types(self):
        schema = {
            "fields": [
                {"fieldname": "customer_name", "label": "Customer Name", "fieldtype": "Data", "reqd": 1, "options": [], "is_layout": False},
                {"fieldname": "budget", "label": "Budget", "fieldtype": "Currency", "reqd": 0, "options": [], "is_layout": False},
                {"fieldname": "approved", "label": "Approved", "fieldtype": "Check", "reqd": 0, "options": [], "is_layout": False},
                {"fieldname": "status", "label": "Status", "fieldtype": "Select", "reqd": 1, "options": ["Draft", "Approved"], "is_layout": False},
            ]
        }

        payload = validate_submission(schema, json.dumps({"customer_name": " ACME ", "budget": "10.5", "approved": 1, "status": "Approved"}))

        self.assertEqual(payload["customer_name"], "ACME")
        self.assertEqual(payload["budget"], 10.5)
        self.assertEqual(payload["approved"], 1)
        self.assertEqual(payload["status"], "Approved")

    def test_validate_submission_rejects_invalid_select(self):
        schema = {
            "fields": [
                {"fieldname": "status", "label": "Status", "fieldtype": "Select", "reqd": 1, "options": ["Draft", "Approved"], "is_layout": False}
            ]
        }

        with self.assertRaises(RuntimeError):
            validate_submission(schema, {"status": "Rejected"})


if __name__ == "__main__":
    unittest.main()

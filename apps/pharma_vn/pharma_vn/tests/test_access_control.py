import json
import unittest
from pathlib import Path
import sys
from types import SimpleNamespace

APP_ROOT = Path(__file__).resolve().parents[2]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from pharma_vn.tests.test_support import install_frappe_stub

frappe = install_frappe_stub()


LABELS = {
    "ACC_DASHBOARD": "Accounting Dashboard",
    "ACC_PAYMENT_ENTRY": "Payment Entry",
    "ACC_JOURNAL_ENTRY": "Journal Entry",
    "WH_STOCK_ENTRY": "Stock Entry",
}


def _fake_get_doc(doctype, name=None):
    if doctype == "Access Group" and name == "Accountant Base":
        return SimpleNamespace(
            permissions_matrix=[
                SimpleNamespace(function_access="ACC_DASHBOARD", access_mode="Allow"),
                SimpleNamespace(function_access="ACC_PAYMENT_ENTRY", access_mode="Allow"),
                SimpleNamespace(function_access="WH_STOCK_ENTRY", access_mode="Deny"),
            ]
        )
    raise AssertionError(f"Unexpected get_doc call: {doctype} {name}")


frappe.get_doc = _fake_get_doc
frappe.db.get_value = lambda doctype, name, fieldname=None: LABELS.get(name) if doctype == "Function Access" else None

from pharma_vn.access_control.service import resolve_profile_access, refresh_profile_resolution


class AccessControlServiceTest(unittest.TestCase):
    def test_group_priority_then_user_override(self):
        profile = SimpleNamespace(
            user="accountant@example.com",
            group_assignments=[
                SimpleNamespace(access_group="Accountant Base", priority=100, is_active=1),
            ],
            user_overrides=[
                SimpleNamespace(function_access="WH_STOCK_ENTRY", access_mode="Allow"),
            ],
        )

        result = resolve_profile_access(profile)
        lookup = {row["function_access"]: row for row in result["effective_permissions"]}

        self.assertEqual(lookup["ACC_DASHBOARD"]["access_mode"], "Allow")
        self.assertEqual(lookup["WH_STOCK_ENTRY"]["access_mode"], "Allow")
        self.assertEqual(lookup["WH_STOCK_ENTRY"]["source"], "user")

    def test_refresh_profile_resolution_writes_json(self):
        profile = SimpleNamespace(
            user="accountant@example.com",
            group_assignments=[SimpleNamespace(access_group="Accountant Base", priority=100, is_active=1)],
            user_overrides=[],
            effective_permissions_json="",
        )

        refresh_profile_resolution(profile)

        parsed = json.loads(profile.effective_permissions_json)
        self.assertEqual(parsed["user"], "accountant@example.com")
        self.assertTrue(any(row["function_access"] == "ACC_PAYMENT_ENTRY" for row in parsed["effective_permissions"]))


if __name__ == "__main__":
    unittest.main()

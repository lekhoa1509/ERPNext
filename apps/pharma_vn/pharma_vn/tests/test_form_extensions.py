import unittest
from pathlib import Path
import sys
from types import SimpleNamespace

APP_ROOT = Path(__file__).resolve().parents[2]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from pharma_vn.tests.test_support import install_frappe_stub

frappe = install_frappe_stub()


class _Field:
    def __init__(self, fieldname, label="", fieldtype="Data", options="", reqd=0):
        self.fieldname = fieldname
        self.label = label
        self.fieldtype = fieldtype
        self.options = options
        self.reqd = reqd


frappe.get_meta = lambda doctype: SimpleNamespace(
    fields=[
        _Field("customer_name", "Customer Name"),
        _Field("territory", "Territory"),
        _Field("notes", "Notes", "Small Text"),
    ]
)
frappe.db.exists = lambda doctype, filters=None, *args, **kwargs: False

from pharma_vn.dynamic_forms.extension_service import (
    announce_extension_update,
    build_extension_plan,
    build_managed_fieldname,
)


class FormExtensionServiceTest(unittest.TestCase):
    def test_build_managed_fieldname_namespaces_extension_fields(self):
        managed = build_managed_fieldname("Customer Addon", "Approval Note")
        self.assertEqual(managed, "ext_customer_addon_approval_note")

    def test_build_extension_plan_generates_fieldnames_and_table_options(self):
        doc = SimpleNamespace(
            extension_name="Customer Addon",
            name="Customer Addon",
            target_doctype="Customer",
            extension_fields=[
                SimpleNamespace(
                    label="Approval Note",
                    fieldtype="Small Text",
                    reference_fieldname="approval_note",
                    insert_after="territory",
                    reqd=0,
                    options="",
                    link_doctype="",
                    table_doctype="",
                    description="",
                    default_value="",
                    allow_on_submit=1,
                    in_list_view=0,
                    hidden=0,
                    custom_field_name="",
                ),
                SimpleNamespace(
                    label="Contacts Table",
                    fieldtype="Table",
                    reference_fieldname="contacts_table",
                    insert_after="ext_customer_addon_approval_note",
                    reqd=0,
                    options="",
                    link_doctype="",
                    table_doctype="Contact Phone",
                    description="",
                    default_value="",
                    allow_on_submit=0,
                    in_list_view=0,
                    hidden=0,
                    custom_field_name="",
                ),
            ],
        )

        plan = build_extension_plan(doc)

        self.assertEqual(plan["rows"][0]["fieldname"], "ext_customer_addon_approval_note")
        self.assertEqual(plan["rows"][1]["options"], "Contact Phone")
        self.assertEqual(doc.extension_fields[1].custom_field_name, "ext_customer_addon_contacts_table")

    def test_build_extension_plan_rejects_unknown_anchor(self):
        doc = SimpleNamespace(
            extension_name="Customer Addon",
            name="Customer Addon",
            target_doctype="Customer",
            extension_fields=[
                SimpleNamespace(
                    label="Approval Note",
                    fieldtype="Small Text",
                    reference_fieldname="approval_note",
                    insert_after="missing_anchor",
                    reqd=0,
                    options="",
                    link_doctype="",
                    table_doctype="",
                    description="",
                    default_value="",
                    allow_on_submit=0,
                    in_list_view=0,
                    hidden=0,
                    custom_field_name="",
                )
            ],
        )

        with self.assertRaises(RuntimeError):
            build_extension_plan(doc)

    def test_announce_extension_update_creates_summary(self):
        captured = []

        class _Notification:
            def __init__(self, payload):
                self.payload = payload

            def insert(self, ignore_permissions=False):
                captured.append(self.payload)
                return self

        frappe.session.user = "owner@example.com"
        frappe.session.user_fullname = "Owner User"
        frappe.get_all = lambda doctype, **kwargs: ["owner@example.com", "other@example.com"]
        frappe.get_doc = lambda payload: _Notification(payload)

        doc = SimpleNamespace(name="Customer Addon", extension_name="Customer Addon")
        plan = {"target_doctype": "Customer", "rows": [{"fieldname": "ext_customer_addon_approval_note"}]}

        announcement = announce_extension_update(doc, plan)

        self.assertEqual(announcement["reload_required"], 1)
        self.assertEqual(announcement["users_notified"], 2)
        self.assertEqual(len(captured), 2)
        self.assertEqual(captured[0]["doctype"], "Notification Log")


if __name__ == "__main__":
    unittest.main()

import importlib
import unittest
from pathlib import Path
import sys
from types import SimpleNamespace

APP_ROOT = Path(__file__).resolve().parents[2]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from pharma_vn.tests.test_support import install_frappe_stub


class CustomerRiskServiceTest(unittest.TestCase):
    def setUp(self):
        self.frappe = install_frappe_stub()
        self.frappe.conf = {}
        self.module = importlib.reload(importlib.import_module("pharma_vn.risk_assessment.service"))

    def test_normalize_risk_payload_infers_high_level_and_reasons(self):
        payload = {
            "score": 72,
            "factors": ["Late payment history", "High outstanding debt"],
        }

        normalized = self.module.normalize_risk_payload(payload, customer="CUST-1", tax_code="0101234567")

        self.assertEqual(normalized["risk_score"], 72)
        self.assertEqual(normalized["risk_level"], "HIGH")
        self.assertEqual(normalized["reasons"][0], "Late payment history")
        self.assertEqual(normalized["tax_code"], "0101234567")

    def test_is_profile_fresh_respects_cache_ttl(self):
        self.frappe.conf["risk_cache_ttl_minutes"] = 120
        fresh_profile = SimpleNamespace(last_check_date="2026-04-08 08:15:00")
        stale_profile = SimpleNamespace(last_check_date="2026-04-08 05:30:00")

        self.assertTrue(self.module.is_profile_fresh(fresh_profile))
        self.assertFalse(self.module.is_profile_fresh(stale_profile))

    def test_build_profile_response_parses_history_and_business_profile(self):
        self.module.list_customer_risk_history = lambda customer, limit=5: [
            {"name": "RISK-1", "risk_score": 55, "risk_level": "WARNING", "last_check_date": "2026-04-07 10:00:00", "reasons": ["Open debt"]},
        ]
        profile = SimpleNamespace(
            name="RISK-2",
            customer="CUST-1",
            tax_code="0101234567",
            risk_score=72,
            risk_level="HIGH",
            last_check_date="2026-04-08 09:00:00",
            reasons="Late payment history\nHigh outstanding debt",
            raw_response='{"risk_engine":{"score":72},"business_profile":{"company_name":"Viet An Pharma","tax_code":"0101234567"}}',
        )

        response = self.module.build_profile_response(profile, from_cache=True)

        self.assertEqual(response["risk_level"], "HIGH")
        self.assertEqual(response["business_profile"]["company_name"], "Viet An Pharma")
        self.assertEqual(len(response["history"]), 1)
        self.assertEqual(response["from_cache"], 1)
        self.assertEqual(response["customer_updates"], {})

    def test_normalize_business_profile_maps_xinvoice_payload(self):
        profile = self.module.normalize_business_profile(
            {
                "orgType": "Doanh nghiep / Don vi su nghiep cong lap",
                "taxID": "0319488060",
                "name": "CONG TY TNHH VI MOC VIET",
                "address": "Tang 5, 70 Pham Ngoc Thach, TP Ho Chi Minh",
                "ngayThanhLap": "12/03/2024",
                "nganhNgheKinhDoanh": ["Phan phoi duoc pham", "Bat dong san"],
                "taxDepartment": "Thue co so 3 Thanh pho Ho Chi Minh",
                "status": "NNT dang hoat dong",
                "updatedAt": "2026-04-10T17:06:23.000Z",
            }
        )

        self.assertEqual(profile["tax_code"], "0319488060")
        self.assertEqual(profile["company_name"], "CONG TY TNHH VI MOC VIET")
        self.assertEqual(profile["organization_type"], "Doanh nghiep / Don vi su nghiep cong lap")
        self.assertEqual(profile["tax_department"], "Thue co so 3 Thanh pho Ho Chi Minh")
        self.assertEqual(profile["established_date"], "2024-03-12")
        self.assertEqual(profile["business_lines"], ["Phan phoi duoc pham", "Bat dong san"])
        self.assertEqual(profile["updated_at"], "2026-04-10T17:06:23.000Z")

    def test_normalize_risk_payload_adds_establishment_and_industry_risk_signals(self):
        normalized = self.module.normalize_risk_payload(
            {
                "score": 18,
                "reasons": ["Healthy payment behavior"],
            },
            customer="CUST-1",
            tax_code="0101234567",
            business_profile={
                "company_name": "Cong Ty ABC",
                "established_date": "2026-01-15",
                "business_lines": ["Bat dong san"],
            },
        )

        self.assertEqual(normalized["risk_score"], 52)
        self.assertEqual(normalized["risk_level"], "WARNING")
        self.assertIn("Business was established less than 12 months ago.", normalized["reasons"])
        self.assertIn("Registered business line indicates elevated risk: Bat dong san.", normalized["reasons"])

    def test_quick_create_customer_from_tax_id_returns_existing_customer(self):
        self.module._resolve_customer_name = lambda customer=None, tax_code=None: "CUST-0001"
        self.frappe.db.get_value = lambda doctype, name, fieldname: "Cong Ty Da Ton Tai"

        response = self.module.quick_create_customer_from_tax_id("0319488060")

        self.assertEqual(response["status"], "existing")
        self.assertEqual(response["customer"], "CUST-0001")
        self.assertEqual(response["customer_name"], "Cong Ty Da Ton Tai")

    def test_quick_create_customer_from_tax_id_creates_customer_from_business_profile(self):
        created_customer = {}

        class FakeCustomerDoc:
            def __init__(self, payload):
                created_customer.update(payload)
                self.name = "CUST-NEW"

            def insert(self, ignore_permissions=True):
                return self

        self.module._resolve_customer_name = lambda customer=None, tax_code=None: ""
        self.module.fetch_tax_business_profile = lambda tax_code: (
            {
                "company_name": "Cong Ty TNHH Vi Moc Viet",
                "tax_code": "0319488060",
                "address": "70 Pham Ngoc Thach, TP HCM",
                "source": "XInvoice Tax API",
            },
            None,
        )
        self.module._get_default_customer_group = lambda: "Commercial"
        self.module._get_default_territory = lambda: "Vietnam"
        self.frappe.db.has_column = lambda doctype, fieldname: fieldname in {"tax_id", "naming_series"}
        self.module.sync_customer_business_profile = lambda customer, business_profile, tax_code=None: {
            "customer_name": "Cong Ty TNHH Vi Moc Viet",
            "tax_id": "0319488060",
            "customer_primary_address": "ADDR-NEW",
        }
        self.frappe.get_doc = lambda payload: FakeCustomerDoc(payload)

        response = self.module.quick_create_customer_from_tax_id("0319488060", customer_type="company")

        self.assertEqual(response["status"], "created")
        self.assertEqual(response["customer"], "CUST-NEW")
        self.assertEqual(response["customer_group"], "Commercial")
        self.assertEqual(response["territory"], "Vietnam")
        self.assertEqual(created_customer["customer_name"], "Cong Ty TNHH Vi Moc Viet")
        self.assertEqual(created_customer["customer_type"], "Company")
        self.assertEqual(created_customer["tax_id"], "0319488060")
        self.assertEqual(created_customer["naming_series"], "CM-.####")

    def test_get_business_profile_api_config_defaults_to_xinvoice(self):
        config = self.module.get_business_profile_api_config()

        self.assertEqual(config["endpoint"], "https://api.xinvoice.vn/gdt-api/tax-payer/{tax_code}")
        self.assertEqual(config["method"], "GET")
        self.assertEqual(config["source"], "XInvoice Tax API")

    def test_normalize_risk_payload_coerces_iso_datetime_with_timezone(self):
        normalized = self.module.normalize_risk_payload(
            {
                "score": 18,
                "checked_at": "2026-04-10T16:38:54.943364+00:00",
                "reasons": ["Healthy payment behavior"],
            },
            customer="CUST-1",
            tax_code="SAFE001",
        )

        self.assertEqual(str(normalized["last_check_date"]), "2026-04-10 16:38:54.943364")

    def test_block_high_risk_sales_order_raises(self):
        self.module.get_latest_customer_risk_profile = lambda customer: SimpleNamespace(
            name="RISK-HIGH",
            risk_score=85,
            risk_level="HIGH",
            last_check_date="2026-04-08 09:00:00",
            reasons="Late payment history",
        )

        with self.assertRaises(RuntimeError):
            self.module.block_high_risk_sales_order(SimpleNamespace(customer="CUST-1"))

    def test_resolve_customer_name_skips_missing_tax_code_column(self):
        self.frappe.db.has_column = lambda doctype, fieldname: fieldname == "tax_id"

        def fake_get_value(doctype, filters_or_name, fieldname):
            self.assertEqual(doctype, "Customer")
            self.assertEqual(filters_or_name, {"tax_id": "0101234567"})
            self.assertEqual(fieldname, "name")
            return "CUST-0001"

        self.frappe.db.get_value = fake_get_value

        customer_name = self.module._resolve_customer_name(tax_code="0101234567")
        self.assertEqual(customer_name, "CUST-0001")

    def test_get_customer_tax_code_reads_tax_id_when_tax_code_column_is_missing(self):
        self.frappe.db.has_column = lambda doctype, fieldname: fieldname == "tax_id"

        def fake_get_value(doctype, customer, fieldname):
            self.assertEqual(doctype, "Customer")
            self.assertEqual(customer, "CUST-0001")
            self.assertEqual(fieldname, "tax_id")
            return "0101234567"

        self.frappe.db.get_value = fake_get_value

        tax_code = self.module._get_customer_tax_code("CUST-0001")
        self.assertEqual(tax_code, "0101234567")

    def test_get_business_profile_api_config_prefers_tax_business_api(self):
        self.frappe.conf.update(
            {
                "tax_business_api_url": "https://tax.example/api/company/{tax_code}",
                "tax_business_api_method": "POST",
                "tax_business_api_key": "secret",
                "tax_business_api_timeout": 22,
                "tax_business_api_source": "VN Tax Lookup",
            }
        )

        config = self.module.get_business_profile_api_config()

        self.assertEqual(config["endpoint"], "https://tax.example/api/company/{tax_code}")
        self.assertEqual(config["method"], "POST")
        self.assertEqual(config["api_key"], "secret")
        self.assertEqual(config["timeout"], 22)
        self.assertEqual(config["source"], "VN Tax Lookup")

    def test_should_use_cached_profile_rejects_profile_without_business_profile_when_lookup_enabled(self):
        self.frappe.conf["tax_business_api_url"] = "https://api.xinvoice.vn/gdt-api/tax-payer/{tax_code}"
        profile = SimpleNamespace(
            tax_code="0319488060",
            last_check_date="2026-04-08 08:15:00",
            raw_response='{"risk_engine":{"score":18}}',
        )

        self.assertFalse(self.module.should_use_cached_profile(profile, tax_code="0319488060"))

    def test_should_use_cached_profile_rejects_old_business_profile_source(self):
        self.frappe.conf["tax_business_api_url"] = "https://api.xinvoice.vn/gdt-api/tax-payer/{tax_code}"
        self.frappe.conf["tax_business_api_source"] = "XInvoice Tax API"
        profile = SimpleNamespace(
            tax_code="0319488060",
            last_check_date="2026-04-08 08:15:00",
            raw_response='{"business_profile":{"company_name":"Mock Company","tax_code":"0319488060","address":"123 Test","status":"Active","source":"Mock Tax Business API"}}',
        )

        self.assertFalse(self.module.should_use_cached_profile(profile, tax_code="0319488060"))

    def test_sync_customer_business_profile_updates_blank_customer_fields_and_creates_primary_address(self):
        values = {
            ("Customer", "CUST-0001", "tax_id"): "",
            ("Customer", "CUST-0001", "customer_name"): "",
            ("Customer", "CUST-0001", "customer_primary_address"): "",
        }
        updates = {}
        created_address = {}

        def fake_get_value(doctype, customer, fieldname):
            return values.get((doctype, customer, fieldname))

        def fake_set_value(doctype, customer, fieldname, value, update_modified=False):
            updates[fieldname] = value
            values[(doctype, customer, fieldname)] = value

        class FakeAddressDoc:
            def __init__(self, payload):
                created_address.update(payload)
                self.name = "ADDR-NEW"

            def insert(self, ignore_permissions=True):
                return self

        self.frappe.db.get_value = fake_get_value
        self.frappe.db.set_value = fake_set_value
        self.frappe.get_doc = lambda payload: FakeAddressDoc(payload)

        synced = self.module.sync_customer_business_profile(
            "CUST-0001",
            {
                "company_name": "Viet An Pharma JSC",
                "tax_code": "0101234567",
                "address": "Ho Chi Minh City",
                "source": "VN Tax Lookup",
            },
        )

        self.assertEqual(synced["tax_id"], "0101234567")
        self.assertEqual(synced["customer_name"], "Viet An Pharma JSC")
        self.assertEqual(synced["customer_primary_address"], "ADDR-NEW")
        self.assertEqual(updates["customer_name"], "Viet An Pharma JSC")
        self.assertEqual(updates["customer_primary_address"], "ADDR-NEW")
        self.assertEqual(created_address["doctype"], "Address")
        self.assertEqual(created_address["address_line1"], "Ho Chi Minh City")
        self.assertEqual(created_address["city"], "Ho Chi Minh City")
        self.assertEqual(created_address["country"], "Vietnam")
        self.assertEqual(created_address["links"][0]["link_name"], "CUST-0001")

    def test_sync_customer_business_profile_overwrites_existing_customer_fields_and_updates_primary_address(self):
        values = {
            ("Customer", "CUST-0001", "tax_id"): "OLD-TAX",
            ("Customer", "CUST-0001", "customer_name"): "Old Customer Name",
            ("Customer", "CUST-0001", "customer_primary_address"): "ADDR-0001",
            ("Address", "ADDR-0001", "address_title"): "Old Customer Name",
            ("Address", "ADDR-0001", "address_type"): "Shipping",
            ("Address", "ADDR-0001", "address_line1"): "Old Address",
            ("Address", "ADDR-0001", "city"): "",
            ("Address", "ADDR-0001", "country"): "",
        }
        updates = {}

        def fake_get_value(doctype, customer_or_name, fieldname):
            return values.get((doctype, customer_or_name, fieldname))

        def fake_set_value(doctype, customer_or_name, fieldname, value, update_modified=False):
            updates[(doctype, customer_or_name, fieldname)] = value
            values[(doctype, customer_or_name, fieldname)] = value

        self.frappe.db.get_value = fake_get_value
        self.frappe.db.set_value = fake_set_value

        synced = self.module.sync_customer_business_profile(
            "CUST-0001",
            {
                "company_name": "New Legal Name Co., Ltd",
                "tax_code": "0319488060",
                "address": "70 Pham Ngoc Thach, TP HCM",
                "city": "Ho Chi Minh City",
                "country": "Vietnam",
                "source": "XInvoice Tax API",
            },
        )

        self.assertEqual(synced["tax_id"], "0319488060")
        self.assertEqual(synced["customer_name"], "New Legal Name Co., Ltd")
        self.assertEqual(synced["customer_primary_address"], "ADDR-0001")
        self.assertEqual(values[("Address", "ADDR-0001", "address_line1")], "70 Pham Ngoc Thach, TP HCM")
        self.assertEqual(values[("Address", "ADDR-0001", "city")], "Ho Chi Minh City")
        self.assertEqual(values[("Address", "ADDR-0001", "country")], "Vietnam")
        self.assertEqual(values[("Address", "ADDR-0001", "address_type")], "Billing")

    def test_build_registered_address_fields_infers_city_from_address_when_api_does_not_return_it(self):
        fields = self.module._build_registered_address_fields(
            "Viet An Pharma JSC",
            {
                "address": "Tang 5, 70 Pham Ngoc Thach, TP Ho Chi Minh, Vietnam",
            },
            "Tang 5, 70 Pham Ngoc Thach, TP Ho Chi Minh, Vietnam",
            creating=True,
        )

        self.assertEqual(fields["city"], "Ho Chi Minh City")
        self.assertEqual(fields["country"], "Vietnam")

    def test_check_customer_risk_returns_cached_risk_with_business_profile_when_engine_is_unavailable(self):
        cached_profile = SimpleNamespace(
            name="RISK-CACHED",
            customer="CUST-0001",
            tax_code="0319488060",
            risk_score=18,
            risk_level="SAFE",
            last_check_date="2026-04-08 08:15:00",
            reasons="Healthy payment behavior",
            raw_response='{"risk_engine":{"score":18}}',
        )
        saved_raw_response = {}

        self.module.get_latest_customer_risk_profile = lambda customer=None: cached_profile
        self.module.has_business_profile_lookup = lambda: True
        self.module.fetch_tax_business_profile = lambda tax_code: (
            {
                "company_name": "Cong Ty TNHH Vi Moc Viet",
                "tax_code": "0319488060",
                "address": "70 Pham Ngoc Thach, TP HCM",
                "status": "NNT dang hoat dong",
                "organization_type": "Doanh nghiep",
                "tax_department": "Thue co so 3 TP HCM",
                "source": "XInvoice Tax API",
            },
            None,
        )

        def raise_engine_error(**kwargs):
            raise RuntimeError("Could not reach the risk engine at http://host.docker.internal:5053/api/risk/check")

        self.module.call_risk_engine = raise_engine_error
        self.module.list_customer_risk_history = lambda customer, limit=5: []
        self.module.sync_customer_business_profile = lambda customer, business_profile, tax_code=None: {
            "customer_name": "Cong Ty TNHH Vi Moc Viet"
        }
        self.frappe.db.set_value = lambda doctype, name, fieldname, value, update_modified=False: saved_raw_response.update(
            {"doctype": doctype, "name": name, "fieldname": fieldname, "value": value}
        )

        response = self.module.check_customer_risk(customer="CUST-0001", tax_code="0319488060")

        self.assertEqual(response["from_cache"], 1)
        self.assertEqual(response["risk_score"], 18)
        self.assertEqual(response["business_profile"]["company_name"], "Cong Ty TNHH Vi Moc Viet")
        self.assertEqual(response["customer_updates"]["customer_name"], "Cong Ty TNHH Vi Moc Viet")
        self.assertIn("Could not reach the risk engine", response["warnings"][0])
        self.assertEqual(saved_raw_response["doctype"], "Customer Risk Profile")
        self.assertEqual(saved_raw_response["name"], "RISK-CACHED")

    def test_build_engine_unavailable_response_without_cache_returns_business_profile(self):
        response = self.module.build_engine_unavailable_response(
            customer="CUST-0002",
            tax_code="0319488060",
            business_profile={
                "company_name": "Cong Ty TNHH Vi Moc Viet",
                "tax_code": "0319488060",
                "address": "70 Pham Ngoc Thach, TP HCM",
                "source": "XInvoice Tax API",
            },
            warnings=["Risk engine offline"],
        )

        self.assertEqual(response["status"], "ready")
        self.assertIsNone(response["risk_score"])
        self.assertEqual(response["risk_level"], "")
        self.assertEqual(response["business_profile"]["tax_code"], "0319488060")
        self.assertEqual(response["warnings"], ["Risk engine offline"])


if __name__ == "__main__":
    unittest.main()

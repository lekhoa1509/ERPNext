import importlib
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

APP_ROOT = Path(__file__).resolve().parents[2]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from pharma_vn.tests.test_support import install_frappe_stub


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.content = json.dumps(payload).encode()
        self.text = json.dumps(payload)

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class WarehouseLayoutApiTest(unittest.TestCase):
    def setUp(self):
        self.frappe = install_frappe_stub()
        self.layout_doc = SimpleNamespace(
            name="LAYOUT-1",
            total_floors=1,
            total_rails=2,
            total_blocks=2,
            total_depths=1,
            wcs_bridge_url="http://127.0.0.1:5057",
            wcs_bridge_api_key="change-this-api-key",
            plc_gateway_configuration_path="/tmp/plc-simulator.json",
            plc_gateway_configuration_json="",
            activate_all_devices_on_connect=1,
        )
        self.frappe.get_doc = lambda doctype, name=None: self.layout_doc
        self.frappe.get_all = lambda doctype, **kwargs: [
            SimpleNamespace(floor=1, rail=1, block=1, depth=1),
        ] if doctype == "WH Cell" else []
        self.module = importlib.reload(importlib.import_module("pharma_vn.api.warehouse_layout"))

    def test_connect_plc_simulator_initializes_bridge_and_generates_layout_json(self):
        calls = []

        def fake_request(method, url, headers=None, json=None, timeout=None):
            calls.append(
                {
                    "method": method,
                    "url": url,
                    "headers": headers,
                    "json": json,
                    "timeout": timeout,
                }
            )

            if url.endswith("/health"):
                return FakeResponse({"status": "ok", "initialized": False})
            if url.endswith("/api/gateway/initialize"):
                return FakeResponse({"isInitialized": True, "deviceCount": 1, "eventCount": 0})
            if url.endswith("/api/gateway/state"):
                return FakeResponse({"isInitialized": True, "deviceCount": 1, "eventCount": 0})
            if url.endswith("/api/gateway/devices/status"):
                return FakeResponse({"Shuttle01": "Idle"})
            if url.endswith("/api/gateway/devices"):
                return FakeResponse([{"deviceId": "Shuttle01", "status": "Idle"}])

            raise AssertionError(f"Unexpected URL: {url}")

        with patch.object(self.module.requests, "request", side_effect=fake_request):
            result = self.module.connect_plc_simulator(layout_name="LAYOUT-1")

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["actions"], ["gateway_initialized", "devices_activated"])
        initialize_call = next(call for call in calls if call["url"].endswith("/api/gateway/initialize"))
        self.assertEqual(initialize_call["headers"]["X-API-Key"], "change-this-api-key")
        self.assertEqual(initialize_call["json"]["configurationPath"], "/tmp/plc-simulator.json")
        self.assertTrue(initialize_call["json"]["activateAllDevices"])
        generated_layout = json.loads(initialize_call["json"]["warehouseLayoutJson"])
        self.assertEqual(generated_layout["blocks"][0]["blockNumber"], 1)
        self.assertEqual(generated_layout["disabledLocations"][0]["depth"], 1)

    def test_connect_plc_simulator_loads_layout_when_bridge_is_already_initialized(self):
        calls = []

        def fake_request(method, url, headers=None, json=None, timeout=None):
            calls.append((method, url, json))
            if url.endswith("/health"):
                return FakeResponse({"status": "ok", "initialized": True})
            if url.endswith("/api/gateway/layout"):
                return FakeResponse({"loaded": True})
            if url.endswith("/api/gateway/devices/activate-all"):
                return FakeResponse({"activated": True})
            if url.endswith("/api/gateway/state"):
                return FakeResponse({"isInitialized": True, "deviceCount": 1, "eventCount": 3})
            if url.endswith("/api/gateway/devices/status"):
                return FakeResponse({"Shuttle01": "Idle"})
            if url.endswith("/api/gateway/devices"):
                return FakeResponse([{"deviceId": "Shuttle01", "status": "Idle"}])

            raise AssertionError(f"Unexpected URL: {url}")

        with patch.object(self.module.requests, "request", side_effect=fake_request):
            result = self.module.connect_plc_simulator(layout_name="LAYOUT-1")

        self.assertTrue(result["ok"])
        self.assertTrue(result["data"]["initialized_before_connect"])
        self.assertIn("layout_loaded", result["data"]["actions"])
        self.assertIn("devices_activated", result["data"]["actions"])
        self.assertNotIn("gateway_initialized", result["data"]["actions"])


if __name__ == "__main__":
    unittest.main()

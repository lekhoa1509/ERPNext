import importlib
import unittest
from types import SimpleNamespace
from pathlib import Path
import sys

APP_ROOT = Path(__file__).resolve().parents[2]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from pharma_vn.tests.test_support import install_frappe_stub


class WarehouseLayoutServiceTest(unittest.TestCase):
    def setUp(self):
        frappe = install_frappe_stub()
        inserted_docs = []

        class FakeDoc(dict):
            def insert(self, ignore_permissions=False):
                inserted_docs.append(dict(self))
                return self

        frappe.get_doc = lambda values: FakeDoc(values)
        frappe.get_all = lambda *args, **kwargs: []
        frappe.db.set_value = lambda *args, **kwargs: None
        self.inserted_docs = inserted_docs
        self.module = importlib.reload(importlib.import_module("pharma_vn.warehouse_layout_2d.service"))

    def test_build_cell_code_uses_alpha_numeric_grid(self):
        self.assertEqual(self.module.build_cell_code(1, 3, 5, 1), "F1R3B5D1")
        self.assertEqual(self.module.build_cell_code(2, 7, 9, 4), "F2R7B9D4")

    def test_sync_layout_cells_generates_missing_cells(self):
        layout_doc = SimpleNamespace(
            name="LAYOUT-1",
            warehouse="WH-A",
            total_floors=1,
            total_rails=2,
            total_blocks=2,
            total_depths=2,
        )
        self.module.sync_layout_cells(layout_doc)

        self.assertEqual(len(self.inserted_docs), 8)
        self.assertEqual(self.inserted_docs[0]["cell_code"], "F1R1B1D1")

    def test_get_layout_overview_groups_depth_cells_by_position(self):
        layout_doc = SimpleNamespace(
            name="LAYOUT-1",
            layout_name="Main Shuttle Layout",
            warehouse="WH-A",
            company="Test Co",
            total_floors=1,
            total_rails=1,
            total_blocks=1,
            total_depths=2,
        )

        def fake_get_all(doctype, **kwargs):
            if doctype == "WH Cell":
                return [
                    SimpleNamespace(
                        name="CELL-1",
                        cell_code="F1R1B1D1",
                        cell_label="Floor 1 - Rail 1 - Block 1 - Depth 1",
                        floor=1,
                        rail=1,
                        block=1,
                        depth=1,
                        status="Available",
                        capacity_qty=0,
                        notes=None,
                    ),
                    SimpleNamespace(
                        name="CELL-2",
                        cell_code="F1R1B1D2",
                        cell_label="Floor 1 - Rail 1 - Block 1 - Depth 2",
                        floor=1,
                        rail=1,
                        block=1,
                        depth=2,
                        status="Reserved",
                        capacity_qty=0,
                        notes=None,
                    ),
                ]

            if doctype == "WH Cell Stock":
                return [
                    SimpleNamespace(
                        cell="CELL-1",
                        item_code="ITEM-001",
                        batch_no="BATCH-1",
                        qty=5,
                        uom="Nos",
                        last_movement_on="2026-04-10 09:00:00",
                    )
                ]

            return []

        self.module.sync_layout_cells = lambda layout: None
        self.module.frappe.get_doc = lambda doctype, name=None: layout_doc
        self.module.frappe.get_all = fake_get_all

        overview = self.module.get_layout_overview("LAYOUT-1")

        self.assertEqual(overview["layout"]["total_depths"], 2)
        self.assertEqual(len(overview["positions"]), 1)
        self.assertEqual(overview["positions"][0]["status"], "Reserved")
        self.assertEqual(overview["positions"][0]["depth_cells"][0]["cell_code"], "F1R1B1D1")

    def test_build_bridge_layout_payload_uses_dimensions_and_blocked_cells(self):
        layout_doc = SimpleNamespace(
            name="LAYOUT-1",
            total_floors=2,
            total_rails=3,
            total_blocks=2,
            total_depths=2,
        )

        self.module.frappe.get_all = lambda doctype, **kwargs: [
            SimpleNamespace(floor=1, rail=2, block=1, depth=2),
            SimpleNamespace(floor=1, rail=2, block=1, depth=2),
            SimpleNamespace(floor=2, rail=3, block=2, depth=1),
        ] if doctype == "WH Cell" else []

        payload = self.module.build_bridge_layout_payload(layout_doc)

        self.assertEqual(len(payload["blocks"]), 2)
        self.assertEqual(payload["blocks"][0]["blockNumber"], 1)
        self.assertEqual(payload["blocks"][0]["maxFloor"], 2)
        self.assertEqual(
            payload["disabledLocations"],
            [
                {"floor": 1, "rail": 2, "block": 1, "depth": 2},
                {"floor": 2, "rail": 3, "block": 2, "depth": 1},
            ],
        )


if __name__ == "__main__":
    unittest.main()

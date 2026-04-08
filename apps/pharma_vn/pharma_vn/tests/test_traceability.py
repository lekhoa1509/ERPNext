import unittest
from pathlib import Path
import sys

APP_ROOT = Path(__file__).resolve().parents[2]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from pharma_vn.services.traceability import summarize_traceability


class TraceabilityTest(unittest.TestCase):
    def test_summarize_traceability_counts_forward_and_backward_links(self):
        summary = summarize_traceability(
            batch_no="BATCH-001",
            batch_status="Released",
            incoming_rows=[
                {"purchase_receipt": "PR-001", "supplier": "SUP-1"},
                {"purchase_receipt": "PR-002", "supplier": "SUP-1"},
            ],
            outgoing_rows=[
                {"delivery_note": "DN-001", "customer": "CUS-1"},
                {"delivery_note": "DN-002", "customer": "CUS-2"},
            ],
        )

        self.assertEqual(summary["supplier_count"], 1)
        self.assertEqual(summary["customer_count"], 2)
        self.assertEqual(summary["incoming_count"], 2)
        self.assertEqual(summary["outgoing_count"], 2)


if __name__ == "__main__":
    unittest.main()

import unittest
from pathlib import Path
import sys

APP_ROOT = Path(__file__).resolve().parents[2]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from pharma_vn.ai_assistant.copilot import build_copilot_reply, detect_copilot_workflow


class AICopilotTest(unittest.TestCase):
    def test_detects_batch_release_workflow(self):
        workflow = detect_copilot_workflow("Please help me release batch ABC after QA")
        self.assertEqual(workflow, "batch_release")

    def test_detects_invoice_compliance_workflow(self):
        workflow = detect_copilot_workflow("review VAT and e-invoice before issuing")
        self.assertEqual(workflow, "invoice_compliance")

    def test_reply_lists_required_fields(self):
        reply = build_copilot_reply("recall_case")
        self.assertIn("company, item_code, batch_no, reason", reply)
        self.assertIn("1. Xac nhan item, batch va ly do thu hoi.", reply)


if __name__ == "__main__":
    unittest.main()

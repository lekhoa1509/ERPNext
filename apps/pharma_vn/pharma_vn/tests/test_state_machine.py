import unittest
from pathlib import Path
import sys

APP_ROOT = Path(__file__).resolve().parents[2]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from pharma_vn.services.state_machine import get_next_states, validate_transition


class StateMachineTest(unittest.TestCase):
    def test_batch_state_machine_allows_draft_to_qa(self):
        self.assertEqual(validate_transition("batch", "Draft", "QA"), "QA")
        self.assertEqual(get_next_states("batch", "QA"), ["Hold", "Rejected", "Released"])

    def test_batch_state_machine_blocks_invalid_jump(self):
        with self.assertRaises(ValueError):
            validate_transition("batch", "Draft", "Released")

    def test_recall_state_machine_requires_order(self):
        self.assertEqual(validate_transition("recall", "Open", "Investigating"), "Investigating")
        with self.assertRaises(ValueError):
            validate_transition("recall", "Open", "Closed")


if __name__ == "__main__":
    unittest.main()

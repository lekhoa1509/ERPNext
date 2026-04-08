import unittest
from pathlib import Path
import sys

APP_ROOT = Path(__file__).resolve().parents[2]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from pharma_vn.services.compliance import (
    build_e_invoice_payload,
    build_vat_summary,
    evaluate_sales_invoice_guardrails,
)


class ComplianceServiceTest(unittest.TestCase):
    def test_build_vat_summary_supports_vietnam_rates(self):
        summary = build_vat_summary(
            [
                {"item_code": "A", "qty": 2, "rate": 100000, "vat_rate": 5},
                {"item_code": "B", "qty": 1, "rate": 50000, "vat_rate": 8},
            ]
        )

        self.assertEqual(summary["taxable_amount"], 250000.0)
        self.assertEqual(summary["vat_amount"], 14000.0)
        self.assertEqual(summary["gross_amount"], 264000.0)

    def test_sales_invoice_guardrails_block_missing_tax_id_for_einvoice(self):
        review = evaluate_sales_invoice_guardrails(
            {
                "company": "Viet An Pharma JSC",
                "customer": "BV-001",
                "posting_date": "2026-04-08",
                "issue_e_invoice": True,
                "items": [{"item_code": "A", "qty": 1, "rate": 100, "vat_rate": 10}],
            }
        )

        self.assertEqual(review["status"], "blocked")
        self.assertTrue(any("Company tax ID" in error for error in review["errors"]))

    def test_build_e_invoice_payload_returns_provider_neutral_payload(self):
        payload = build_e_invoice_payload(
            {
                "company": "Viet An Pharma JSC",
                "company_tax_id": "0312345678",
                "customer": "BV-001",
                "customer_name": "Benh Vien A",
                "customer_tax_id": "0300000001",
                "posting_date": "2026-04-08",
                "issue_e_invoice": True,
                "items": [{"item_code": "A", "qty": 1, "rate": 100000, "vat_rate": 10}],
            }
        )

        self.assertEqual(payload["provider"], "generic")
        self.assertEqual(payload["invoice"]["vat_summary"]["vat_amount"], 10000.0)


if __name__ == "__main__":
    unittest.main()

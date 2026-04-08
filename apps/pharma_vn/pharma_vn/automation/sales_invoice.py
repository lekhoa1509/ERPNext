import frappe
from frappe import _

from pharma_vn.automation.transaction_taxes import sync_transaction_taxes
from pharma_vn.services.compliance import build_e_invoice_payload, evaluate_sales_invoice_guardrails


def validate_sales_invoice(doc, method=None):
    sync_transaction_taxes(doc, method=method)

    # Hook validate la diem tot nhat de chan invoice truoc khi submit len so sach/e-invoice.
    review = evaluate_sales_invoice_guardrails(_build_invoice_context(doc))

    if hasattr(doc, "pharma_compliance_status"):
        doc.pharma_compliance_status = review["status"].title()
    if hasattr(doc, "pharma_compliance_summary"):
        doc.pharma_compliance_summary = _build_review_summary(review)

    if review["errors"]:
        frappe.throw(_("Sales Invoice compliance blocked: {0}").format("; ".join(review["errors"])))


def prepare_e_invoice_payload(doc, method=None):
    if not frappe.db.has_column("Sales Invoice", "e_invoice_status"):
        return

    if doc.get("e_invoice_status") not in {"Submitted", "Issued"}:
        return

    # Chi sinh payload khi invoice da vao giai doan san sang phat hanh e-invoice.
    payload = build_e_invoice_payload(_build_invoice_context(doc))
    if frappe.db.has_column("Sales Invoice", "e_invoice_payload_json"):
        doc.db_set("e_invoice_payload_json", frappe.as_json(payload), update_modified=False)


def _build_invoice_context(doc):
    # Chuan hoa Sales Invoice ve dict thuần de service compliance co the test doc lap.
    return {
        "company": doc.company,
        "company_tax_id": getattr(doc, "company_tax_id", None),
        "customer": doc.customer,
        "customer_name": doc.customer_name,
        "customer_tax_id": getattr(doc, "tax_id", None) or getattr(doc, "customer_tax_id", None),
        "posting_date": str(doc.posting_date) if doc.posting_date else None,
        "invoice_date": str(getattr(doc, "bill_date", None) or doc.posting_date) if doc.posting_date else None,
        "currency": doc.currency,
        "is_return": doc.is_return,
        "return_against": doc.return_against,
        "issue_e_invoice": doc.get("e_invoice_status") in {"Submitted", "Issued"},
        "e_invoice_status": doc.get("e_invoice_status"),
        "e_invoice_no": doc.get("e_invoice_no"),
        "items": [
            {
                "item_code": row.item_code,
                "qty": row.qty,
                "rate": row.rate,
                "net_amount": row.amount,
                "vat_rate": _extract_row_tax_rate(row) or getattr(row, "tax_rate", None) or _extract_tax_rate(doc),
            }
            for row in doc.items
        ],
    }


def _extract_row_tax_rate(row):
    item_tax_rate = getattr(row, "item_tax_rate", None)
    if not item_tax_rate:
        return None

    try:
        payload = frappe.parse_json(item_tax_rate) or {}
    except Exception:
        return None

    rates = sorted(
        {
            int(float(rate))
            for rate in payload.values()
            if rate not in (None, "") and float(rate or 0)
        }
    )
    if len(rates) == 1:
        return rates[0]
    return None


def _extract_tax_rate(doc):
    # Hien tai uu tien thue "On Net Total"; sau nay co the nang cap doc tax theo tung dong.
    for row in doc.get("taxes") or []:
        if row.charge_type == "On Net Total":
            return row.rate
    return 0


def _build_review_summary(review):
    parts = [f"Status: {review['status']}"]
    if review["warnings"]:
        parts.append("Warnings: " + "; ".join(review["warnings"]))
    if review["errors"]:
        parts.append("Errors: " + "; ".join(review["errors"]))
    return " | ".join(parts)

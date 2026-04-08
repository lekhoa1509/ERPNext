from datetime import date


ALLOWED_VAT_RATES = {0, 5, 8, 10}


def normalize_vat_rate(value):
    # Repo hien tai chi khoa cac muc VAT VN dang duoc seed va tai lieu de cap.
    if value in (None, ""):
        return 0

    rate = float(value)
    if rate.is_integer():
        rate = int(rate)
    if rate not in ALLOWED_VAT_RATES:
        raise ValueError(f"Unsupported VAT rate: {value}")
    return rate


def build_vat_summary(items):
    taxable_amount = 0.0
    vat_amount = 0.0
    gross_amount = 0.0
    normalized_rows = []

    for row in items or []:
        # Cho phep caller gui san net_amount, neu khong thi tu tinh tu qty * rate.
        qty = float(row.get("qty") or 0)
        rate = float(row.get("rate") or 0)
        net_amount = float(row.get("net_amount") or qty * rate)
        vat_rate = normalize_vat_rate(row.get("vat_rate", 0))
        row_vat_amount = round(net_amount * float(vat_rate) / 100, 2)
        row_gross_amount = round(net_amount + row_vat_amount, 2)

        taxable_amount += net_amount
        vat_amount += row_vat_amount
        gross_amount += row_gross_amount
        normalized_rows.append(
            {
                "item_code": row.get("item_code"),
                "qty": qty,
                "rate": rate,
                "net_amount": round(net_amount, 2),
                "vat_rate": vat_rate,
                "vat_amount": row_vat_amount,
                "gross_amount": row_gross_amount,
            }
        )

    return {
        "items": normalized_rows,
        "taxable_amount": round(taxable_amount, 2),
        "vat_amount": round(vat_amount, 2),
        "gross_amount": round(gross_amount, 2),
    }


def evaluate_sales_invoice_guardrails(invoice):
    errors = []
    warnings = []

    posting_date = invoice.get("posting_date")
    invoice_date = invoice.get("invoice_date") or posting_date
    today = invoice.get("today") or date.today().isoformat()
    issue_e_invoice = bool(invoice.get("issue_e_invoice"))
    is_return = bool(invoice.get("is_return"))

    if not invoice.get("company"):
        errors.append("Company is required for compliance review.")
    if not invoice.get("customer"):
        errors.append("Customer is required for compliance review.")
    if not posting_date:
        errors.append("Posting Date is required before issuing an invoice.")

    if invoice_date and posting_date and invoice_date < posting_date:
        warnings.append("Invoice date is earlier than posting date and should be reviewed.")
    if posting_date and posting_date > today:
        warnings.append("Posting date is in the future.")

    try:
        vat_summary = build_vat_summary(invoice.get("items") or [])
    except ValueError as exc:
        errors.append(str(exc))
        vat_summary = build_vat_summary([])

    if not vat_summary["items"]:
        errors.append("At least one invoice item is required.")

    if issue_e_invoice:
        # E-invoice la diem compliance nhay cam nhat, nen chan som neu thieu tax identity.
        if not invoice.get("company_tax_id"):
            errors.append("Company tax ID is required for e-invoice issuance.")
        if not invoice.get("customer_tax_id") and not invoice.get("customer_name"):
            errors.append("Customer tax ID or legal customer name is required for e-invoice issuance.")

    if is_return and not invoice.get("return_against"):
        errors.append("Return invoices must reference the original Sales Invoice.")

    if invoice.get("e_invoice_status") == "Issued" and not invoice.get("e_invoice_no"):
        warnings.append("E-invoice status is Issued but e_invoice_no is still empty.")

    # blocked = khong duoc di tiep, review = can nguoi xem lai, ready = co the phat hanh.
    status = "blocked" if errors else "ready"
    if warnings and not errors:
        status = "review"

    return {
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "vat_summary": vat_summary,
        "provider": invoice.get("e_invoice_provider") or "generic",
    }


def build_e_invoice_payload(invoice):
    review = evaluate_sales_invoice_guardrails(invoice)
    if review["status"] == "blocked":
        raise ValueError("; ".join(review["errors"]))

    # Payload nay co y tinh giu neutral de sau nay map sang Viettel/VNPT/MISA de dang hon.
    return {
        "provider": review["provider"],
        "invoice": {
            "posting_date": invoice.get("posting_date"),
            "invoice_date": invoice.get("invoice_date") or invoice.get("posting_date"),
            "company": invoice.get("company"),
            "company_tax_id": invoice.get("company_tax_id"),
            "customer": invoice.get("customer"),
            "customer_name": invoice.get("customer_name"),
            "customer_tax_id": invoice.get("customer_tax_id"),
            "currency": invoice.get("currency") or "VND",
            "is_return": bool(invoice.get("is_return")),
            "return_against": invoice.get("return_against"),
            "vat_summary": review["vat_summary"],
        },
    }

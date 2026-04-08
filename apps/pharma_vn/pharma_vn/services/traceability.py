def summarize_traceability(*, batch_no, batch_status=None, incoming_rows=None, outgoing_rows=None):
    incoming_rows = incoming_rows or []
    outgoing_rows = outgoing_rows or []

    customers = sorted(
        {
            row.get("customer")
            for row in outgoing_rows
            if row.get("customer")
        }
    )
    suppliers = sorted(
        {
            row.get("supplier")
            for row in incoming_rows
            if row.get("supplier")
        }
    )
    return {
        "batch_no": batch_no,
        "batch_status": batch_status,
        "customer_count": len(customers),
        "supplier_count": len(suppliers),
        "customers": customers,
        "suppliers": suppliers,
        "incoming_count": len(incoming_rows),
        "outgoing_count": len(outgoing_rows),
    }

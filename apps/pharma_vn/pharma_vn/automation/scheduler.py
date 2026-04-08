import frappe
from frappe import _
from frappe.utils import add_to_date, cint, now_datetime, nowdate

from pharma_vn.services.alerts import (
    build_alert_event,
    detect_stock_mismatch_rows,
    get_operations_logger,
    make_alert_key,
)


def process_near_expiry_batches():
    alert_days = cint(frappe.db.get_default("pharma_near_expiry_alert_days") or 180)
    target_date = add_to_date(nowdate(), days=alert_days, as_string=True)

    batches = frappe.db.sql(
        """
        select name, item, expiry_date
        from `tabBatch`
        where expiry_date is not null
          and expiry_date between %(today)s and %(target_date)s
        order by expiry_date asc
        limit 100
        """,
        {"today": nowdate(), "target_date": target_date},
        as_dict=True,
    )

    for row in batches:
        message = _("Batch {0} for item {1} expires on {2}").format(
            row.name, row.item, row.expiry_date
        )
        _notify_roles(
            roles=_get_alert_roles(),
            subject=_("Near-expiry batch alert"),
            message=message,
            document_type="Batch",
            document_name=row.name,
        )


def process_temperature_excursions():
    if not frappe.db.exists("DocType", "PH Temperature Log"):
        return

    rows = frappe.get_all(
        "PH Temperature Log",
        filters={"action_required": 1, "notification_sent": 0},
        fields=["name", "warehouse", "batch_no", "temperature_c", "recorded_at"],
        limit=100,
    )

    for row in rows:
        message = _(
            "Temperature excursion detected at warehouse {0}, batch {1}, temperature {2}C."
        ).format(row.warehouse, row.batch_no or "-", row.temperature_c)
        _create_alert(
            alert_key=make_alert_key("temperature_excursion", row.name, "PH Temperature Log"),
            alert_event=build_alert_event(
                alert_type="temperature_excursion",
                severity="High",
                message=message,
                reference_doctype="PH Temperature Log",
                reference_name=row.name,
                payload={"warehouse": row.warehouse, "batch_no": row.batch_no, "temperature_c": row.temperature_c},
            ),
        )
        _notify_roles(
            roles=_get_alert_roles(),
            subject=_("Cold-chain excursion alert"),
            message=message,
            document_type="PH Temperature Log",
            document_name=row.name,
        )
        frappe.db.set_value(
            "PH Temperature Log",
            row.name,
            "notification_sent",
            1,
            update_modified=False,
        )


def process_invoice_failures():
    if not frappe.db.has_column("Sales Invoice", "e_invoice_status"):
        return

    rows = frappe.get_all(
        "Sales Invoice",
        filters={"e_invoice_status": "Failed", "pharma_invoice_alert_sent": 0},
        fields=["name", "customer", "posting_date"],
        limit=100,
    )
    for row in rows:
        message = _("E-invoice issuance failed for Sales Invoice {0}.").format(row.name)
        _create_alert(
            alert_key=make_alert_key("invoice_fail", row.name, "Sales Invoice"),
            alert_event=build_alert_event(
                alert_type="invoice_fail",
                severity="Critical",
                message=message,
                reference_doctype="Sales Invoice",
                reference_name=row.name,
                payload={"customer": row.customer, "posting_date": str(row.posting_date)},
            ),
        )
        _notify_roles(
            roles=_get_alert_roles(),
            subject=_("E-invoice failed"),
            message=message,
            document_type="Sales Invoice",
            document_name=row.name,
        )
        frappe.db.set_value("Sales Invoice", row.name, "pharma_invoice_alert_sent", 1, update_modified=False)


def process_stock_mismatches():
    if not frappe.db.exists("DocType", "WH Cell Stock") or not frappe.db.table_exists("Bin"):
        return

    rows = frappe.db.sql(
        """
        select cell_rows.warehouse, cell_rows.item_code, cell_rows.cell_qty, coalesce(bin.actual_qty, 0) as bin_qty
        from (
            select warehouse, item_code, sum(qty) as cell_qty
            from `tabWH Cell Stock`
            group by warehouse, item_code
        ) cell_rows
        left join `tabBin` bin on bin.warehouse = cell_rows.warehouse and bin.item_code = cell_rows.item_code
        """,
        as_dict=True,
    )
    mismatches = detect_stock_mismatch_rows(rows)
    for row in mismatches[:100]:
        message = _(
            "Stock mismatch detected for item {0} at warehouse {1}: cell qty {2}, bin qty {3}."
        ).format(row["item_code"], row["warehouse"], row["cell_qty"], row["bin_qty"])
        _create_alert(
            alert_key=make_alert_key("stock_mismatch", row["item_code"], row["warehouse"], str(row["difference"])),
            alert_event=build_alert_event(
                alert_type="stock_mismatch",
                severity="High",
                message=message,
                reference_doctype="Warehouse",
                reference_name=row["warehouse"],
                payload=row,
            ),
        )
        _notify_roles(
            roles=_get_alert_roles(),
            subject=_("Stock mismatch alert"),
            message=message,
            document_type="Warehouse",
            document_name=row["warehouse"],
        )


def _get_alert_roles():
    return [
        frappe.db.get_default("pharma_alert_role_primary") or "QA Manager",
        frappe.db.get_default("pharma_alert_role_secondary") or "Warehouse Manager",
    ]


def _notify_roles(roles, subject, message, document_type=None, document_name=None):
    users = set()
    for role in roles:
        role_users = frappe.get_all(
            "Has Role",
            filters={"role": role, "parenttype": "User"},
            pluck="parent",
        )
        users.update(role_users)

    for user in users:
        notification = frappe.get_doc(
            {
                "doctype": "Notification Log",
                "for_user": user,
                "type": "Alert",
                "subject": subject,
                "email_content": message,
                "document_type": document_type,
                "document_name": document_name,
            }
        )
        notification.insert(ignore_permissions=True)


def _create_alert(*, alert_key, alert_event):
    logger = get_operations_logger()
    logger.warning("%s %s", alert_key, alert_event["message"])

    if not frappe.db.exists("DocType", "PH Alert Log"):
        return

    if frappe.db.exists("PH Alert Log", {"alert_key": alert_key}):
        alert_name = frappe.db.get_value("PH Alert Log", {"alert_key": alert_key}, "name")
        frappe.db.set_value(
            "PH Alert Log",
            alert_name,
            {
                "message": alert_event["message"],
                "severity": alert_event["severity"],
                "payload_json": alert_event["payload_json"],
                "last_triggered_on": now_datetime(),
                "status": "Open",
            },
            update_modified=False,
        )
        return

    frappe.get_doc(
        {
            "doctype": "PH Alert Log",
            "alert_key": alert_key,
            "alert_type": alert_event["alert_type"],
            "severity": alert_event["severity"],
            "status": "Open",
            "message": alert_event["message"],
            "reference_doctype": alert_event["reference_doctype"],
            "reference_name": alert_event["reference_name"],
            "payload_json": alert_event["payload_json"],
            "last_triggered_on": now_datetime(),
        }
    ).insert(ignore_permissions=True)

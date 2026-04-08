import frappe
from frappe import _
from frappe.utils import now_datetime

from pharma_vn.automation.transaction_taxes import sync_transaction_taxes


CHANNEL_MAP = {
    "Hospital": "Hospital",
    "Clinic": "Clinic",
    "Pharmacy": "Pharmacy",
    "Distributor": "Distributor",
    "B2C": "B2C",
}


def validate_sales_order(doc, method=None):
    sync_transaction_taxes(doc, method=method)
    _sync_overview_fields(doc)
    _sync_customer_defaults(doc)
    _sync_status_fields(doc)
    _sync_discount_fields(doc)
    _sync_workflow_audit(doc)
    _validate_rejection_reason(doc)


@frappe.whitelist()
def check_credit_status(sales_order):
    doc = frappe.get_doc("Sales Order", sales_order)
    status = _resolve_credit_status(doc)
    outstanding = _get_customer_outstanding(doc.customer, doc.company)
    credit_limit = _get_customer_credit_limit(doc.customer, doc.company)
    available_credit = None if credit_limit is None else credit_limit - outstanding - (doc.grand_total or 0)

    doc.db_set("pharma_credit_status", status, update_modified=False)
    frappe.db.commit()

    return {
        "customer": doc.customer,
        "credit_status": status,
        "credit_limit": credit_limit,
        "outstanding": outstanding,
        "order_value": doc.grand_total,
        "available_credit": available_credit,
    }


@frappe.whitelist()
def log_order_confirmation(sales_order):
    doc = frappe.get_doc("Sales Order", sales_order)
    doc.db_set("pharma_last_confirmation_sent_on", now_datetime(), update_modified=False)
    doc.db_set(
        "pharma_last_confirmation_sent_to",
        doc.contact_email or frappe.session.user,
        update_modified=False,
    )
    frappe.db.commit()
    return {"sales_order": doc.name, "status": "logged"}


def _sync_overview_fields(doc):
    contact_phone, contact_email = _get_contact_channels(
        doc.contact_person,
        fallback_phone=doc.contact_phone or doc.contact_mobile,
        fallback_email=doc.contact_email,
    )
    doc.pharma_account_name = doc.customer_name or doc.customer
    doc.pharma_account_address = _clean_text(doc.address_display)
    doc.pharma_contact_name = _get_contact_label(doc.contact_person, doc.contact_display)
    doc.pharma_contact_phone = contact_phone
    doc.pharma_contact_email = contact_email
    doc.pharma_ship_to_name = _get_address_label(doc.shipping_address_name) or doc.customer_name or doc.customer
    doc.pharma_ship_to_address = _clean_text(doc.shipping_address)
    doc.pharma_bill_to_name = _get_address_label(doc.customer_address) or doc.customer_name or doc.customer
    doc.pharma_bill_to_address = _clean_text(doc.address_display)

    if contact_phone and not doc.contact_phone:
        doc.contact_phone = contact_phone
    if contact_email and not doc.contact_email:
        doc.contact_email = contact_email

    if doc.pharma_external_reference and not doc.po_no:
        doc.po_no = doc.pharma_external_reference
    elif doc.po_no and not doc.pharma_external_reference:
        doc.pharma_external_reference = doc.po_no

    if not doc.pharma_requested_date:
        doc.pharma_requested_date = doc.delivery_date or doc.transaction_date
    if not doc.pharma_issue_date:
        doc.pharma_issue_date = doc.transaction_date
    if not doc.pharma_price_basis:
        doc.pharma_price_basis = "Net"
    if not doc.pharma_origin:
        doc.pharma_origin = "Manual Entry"
    if not doc.pharma_delivery_priority:
        doc.pharma_delivery_priority = "Normal"
    if not doc.pharma_payment_reference_type:
        doc.pharma_payment_reference_type = "Customer PO"
    if not doc.pharma_approval_status:
        doc.pharma_approval_status = "In Preparation"

    if doc.named_place and not doc.pharma_incoterms_location:
        doc.pharma_incoterms_location = doc.named_place


def _sync_customer_defaults(doc):
    if not doc.customer:
        return

    customer = frappe.get_cached_doc("Customer", doc.customer)
    doc.pharma_distribution_channel = (
        doc.pharma_distribution_channel
        or CHANNEL_MAP.get(customer.customer_channel)
        or "Distributor"
    )
    doc.pharma_sales_unit = doc.pharma_sales_unit or customer.sales_region or customer.territory
    doc.pharma_sales_organization = doc.pharma_sales_organization or doc.company

    if not doc.pharma_employee_responsible:
        employee = frappe.db.get_value("Employee", {"user_id": doc.owner}, "name")
        if employee:
            doc.pharma_employee_responsible = employee

    doc.pharma_credit_status = _resolve_credit_status(doc, customer=customer)


def _sync_status_fields(doc):
    doc.pharma_delivery_status = doc.delivery_status or "Not Started"
    doc.pharma_invoice_status = doc.billing_status or "Not Started"

    if doc.reserve_stock:
        if (doc.per_picked or 0) >= 100:
            doc.pharma_allocation_status = "Fully Reserved"
        elif (doc.per_picked or 0) > 0:
            doc.pharma_allocation_status = "Partially Reserved"
        else:
            doc.pharma_allocation_status = "Pending Allocation"
    else:
        doc.pharma_allocation_status = "Not Reserved"

    workflow_state = getattr(doc, "workflow_state", None)
    if workflow_state:
        doc.pharma_approval_status = workflow_state


def _sync_discount_fields(doc):
    if doc.additional_discount_percentage and not doc.pharma_total_discount_percent:
        doc.pharma_total_discount_percent = doc.additional_discount_percentage
    elif doc.pharma_total_discount_percent and not doc.additional_discount_percentage:
        doc.additional_discount_percentage = doc.pharma_total_discount_percent

    if doc.discount_amount and not doc.pharma_total_discount_amount:
        doc.pharma_total_discount_amount = doc.discount_amount
    elif doc.pharma_total_discount_amount and not doc.discount_amount:
        doc.discount_amount = doc.pharma_total_discount_amount


def _sync_workflow_audit(doc):
    workflow_state = getattr(doc, "workflow_state", None)
    if workflow_state != "Approved":
        return

    previous = doc.get_doc_before_save()
    previous_state = getattr(previous, "workflow_state", None) if previous else None
    if previous_state != workflow_state:
        doc.pharma_last_approved_by = frappe.session.user
        doc.pharma_last_approved_on = now_datetime()


def _validate_rejection_reason(doc):
    workflow_state = getattr(doc, "workflow_state", None)
    if workflow_state == "Rejected" and not doc.pharma_rejection_reason:
        frappe.throw(_("Reason for Rejection is required before moving the order to Rejected."))


def _resolve_credit_status(doc, customer=None):
    customer = customer or frappe.get_cached_doc("Customer", doc.customer)
    base_status = {
        "Approved": "Approved",
        "Blocked": "Blocked",
        "Pending": "Under Review",
        None: "Not Checked",
    }.get(customer.credit_review_status, "Not Checked")

    credit_limit = _get_customer_credit_limit(doc.customer, doc.company)
    outstanding = _get_customer_outstanding(doc.customer, doc.company)
    if credit_limit is not None and (outstanding + (doc.grand_total or 0)) > credit_limit:
        return "Over Limit"

    return base_status


def _get_customer_credit_limit(customer, company):
    if frappe.db.table_exists("Customer Credit Limit"):
        credit_limit = frappe.db.get_value(
            "Customer Credit Limit",
            {"parent": customer, "company": company},
            "credit_limit",
        )
        if credit_limit is not None:
            return flt_or_none(credit_limit)
    return None


def _get_customer_outstanding(customer, company):
    if not frappe.db.table_exists("Sales Invoice"):
        return 0

    outstanding = frappe.db.sql(
        """
        select coalesce(sum(outstanding_amount), 0)
        from `tabSales Invoice`
        where customer = %s and company = %s and docstatus = 1
        """,
        (customer, company),
    )[0][0]
    return flt_or_none(outstanding) or 0


def flt_or_none(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clean_text(value):
    return (value or "").replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")


def _get_address_label(address_name):
    if not address_name:
        return None

    return frappe.db.get_value("Address", address_name, "address_title") or address_name


def _get_contact_label(contact_name, contact_display=None):
    if contact_display:
        return contact_display
    if not contact_name:
        return None

    return frappe.db.get_value("Contact", contact_name, "first_name") or contact_name


def _get_contact_channels(contact_name, fallback_phone=None, fallback_email=None):
    if not contact_name:
        return fallback_phone, fallback_email

    contact = frappe.get_cached_doc("Contact", contact_name)
    phone = fallback_phone or contact.get("phone") or contact.get("mobile_no")
    email = fallback_email or contact.get("email_id")

    if not email:
        primary_email = next((row.email_id for row in contact.get("email_ids") if row.is_primary), None)
        email = primary_email or (contact.get("email_ids")[0].email_id if contact.get("email_ids") else None)

    if not phone:
        primary_phone = next((row.phone for row in contact.get("phone_nos") if row.is_primary_phone), None)
        phone = primary_phone or (contact.get("phone_nos")[0].phone if contact.get("phone_nos") else None)

    return phone, email

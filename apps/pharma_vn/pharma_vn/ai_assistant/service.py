import json
import re
import unicodedata
from pathlib import Path

import frappe
import requests
from frappe import _
from frappe.utils import cint, cstr, flt, getdate, nowdate

from pharma_vn.ai_assistant import config as assistant_config
from pharma_vn.ai_assistant.copilot import build_copilot_reply, detect_copilot_workflow
from pharma_vn.customer_naming import CUSTOMER_NAMING_SERIES


DEFAULT_AI_MODEL = assistant_config.MODEL or assistant_config.DEFAULT_OPENAI_MODEL
ASSISTANT_SKILL_REFERENCE = (
    Path(__file__).resolve().parent / "references" / "erpnext_vn_ops_skill.md"
)
REPORT_FREQUENCY_MAP = {
    "daily": "Daily",
    "weekdays": "Weekdays",
    "weekly": "Weekly",
    "monthly": "Monthly",
}
REPORT_FORMAT_MAP = {
    "html": "HTML",
    "xlsx": "XLSX",
    "csv": "CSV",
    "pdf": "PDF",
}
SUPPORTED_INTENTS = {
    "create_customer",
    "create_sales_order_draft",
    "create_auto_email_report",
    "erp_workflow_copilot",
    "stock_lookup",
    "help",
    "unknown",
}
CUSTOMER_TYPE_MAP = {
    "company": "Company",
    "cong ty": "Company",
    "to chuc": "Company",
    "organization": "Company",
    "hospital": "Company",
    "clinic": "Company",
    "pharmacy": "Company",
    "distributor": "Company",
    "individual": "Individual",
    "ca nhan": "Individual",
    "customer": "Individual",
    "retail": "Individual",
    "b2c": "Individual",
}
CUSTOMER_CHANNEL_MAP = {
    "hospital": "Hospital",
    "benh vien": "Hospital",
    "clinic": "Clinic",
    "phong kham": "Clinic",
    "pharmacy": "Pharmacy",
    "nha thuoc": "Pharmacy",
    "drugstore": "Pharmacy",
    "distributor": "Distributor",
    "nha phan phoi": "Distributor",
    "b2c": "B2C",
    "retail": "B2C",
    "khach le": "B2C",
}
LOCAL_HELP_PATTERNS = [
    {
        "topic": "sales_flow",
        "keywords": [
            "quy trinh ban hang",
            "len don hang ban",
            "len don ban hang",
            "don hang ban",
            "sales order",
            "bao gia",
            "quotation",
            "delivery note",
            "sales invoice",
        ],
    },
    {
        "topic": "purchase_flow",
        "keywords": [
            "quy trinh mua hang",
            "mua hang",
            "purchase order",
            "purchase receipt",
            "purchase invoice",
            "nhap hang nha cung cap",
        ],
    },
    {
        "topic": "inventory_issue",
        "keywords": [
            "xuat kho",
            "xuat hang",
            "material issue",
        ],
    },
    {
        "topic": "inventory_receipt",
        "keywords": [
            "nhap kho",
            "material receipt",
            "nhap hang noi bo",
        ],
    },
    {
        "topic": "inventory_transfer",
        "keywords": [
            "chuyen kho",
            "material transfer",
            "quarantine sang released",
            "chuyen tu quarantine",
        ],
    },
    {
        "topic": "invoice_flow",
        "keywords": [
            "hoa don",
            "invoice",
            "e-invoice",
            "hoa don dien tu",
            "sales invoice",
            "purchase invoice",
        ],
    },
    {
        "topic": "stock_check",
        "keywords": [
            "kiem tra ton kho",
            "xem ton kho",
            "stock balance",
            "warehouse wise stock balance",
            "stock ledger",
            "ton kho",
        ],
    },
    {
        "topic": "legal_guidance",
        "keywords": [
            "nghi dinh",
            "thong tu",
            "luat",
            "vat",
            "thue",
            "quy dinh",
            "phap ly",
        ],
    },
]


def get_assistant_bootstrap():
    settings = _get_settings()
    configured = bool(_get_ai_api_key(settings))
    enabled = bool(cint(settings.enabled))
    provider_name = _get_provider_name(settings)
    api_key_env_var = _get_api_key_env_var(settings)
    user_email = _get_current_user_email() or _first_email_from_defaults(settings) or "your-email@example.com"

    customer_example = _get_customer_options(limit=1)
    item_example = _get_item_options(limit=1)
    warehouse_example = _get_warehouse_options(limit=1)

    customer_name = customer_example[0]["label"] if customer_example else "Benh Vien Binh Dan"
    item_name = item_example[0]["name"] if item_example else "PARA-500"
    warehouse_name = warehouse_example[0]["name"] if warehouse_example else "HCM Sellable - VAP"

    if not enabled:
        welcome_message = "AI Assistant is disabled in .env."
    elif not configured:
        welcome_message = (
            f"{provider_name} API key is not configured in .env yet. Update {api_key_env_var} in the local .env file, then ask "
            "about sales, purchase, warehouse, invoice flows, stock checks, or quick ERP actions."
        )
    else:
        welcome_message = (
            "Ask me about sales, purchase, warehouse, invoice flows, stock checks, or let me create "
            "customers, draft orders, and reports."
        )

    return {
        "enabled": enabled,
        "configured": configured,
        "model": cstr(settings.model).strip() or DEFAULT_AI_MODEL,
        "provider_name": provider_name,
        "api_key_env_var": api_key_env_var,
        "current_user_name": _get_current_user_label(),
        "welcome_message": welcome_message,
        "sample_prompts": [
            "Quy trinh ban hang tren ERPNext di theo chung tu nao?",
            f"Create a draft sales order for {customer_name} with 20 {item_name}",
            f"Check stock for {item_name} in {warehouse_name}",
            "Khi nao dung Delivery Note va khi nao dung Sales Invoice?",
        ],
    }


def chat_with_assistant(message, history=None):
    settings = _get_settings()
    bootstrap = get_assistant_bootstrap()

    if not cint(settings.enabled):
        return _assistant_result(
            status="error",
            reply="AI Assistant dang tat trong file .env.",
            bootstrap=bootstrap,
        )

    if not _get_ai_api_key(settings):
        return _assistant_result(
            status="error",
            reply=_("Chua khai bao {0} API key trong file .env ({1}).").format(
                _get_provider_name(settings), _get_api_key_env_var(settings)
            ),
            bootstrap=bootstrap,
        )

    plan = interpret_user_message(message=message, history=history or [], settings=settings)
    result = execute_assistant_intent(plan, settings=settings)
    result["plan"] = plan
    result["bootstrap"] = bootstrap
    return result


def interpret_user_message(message, history=None, settings=None):
    settings = settings or _get_settings()
    history = _sanitize_history(history or [])
    stock_lookup_plan = _build_local_stock_lookup_plan(message)
    if stock_lookup_plan:
        return stock_lookup_plan
    # Local routing duoc uu tien de cac cau hoi SOP/nghiep vu co phan hoi nhanh va on dinh.
    local_plan = _build_local_help_plan(message)
    if local_plan:
        return local_plan
    # Workflow copilot duoc bat truoc khi goi model de tranh ton token cho case da biet mau.
    copilot_plan = _build_local_copilot_plan(message)
    if copilot_plan:
        return copilot_plan
    context = _build_runtime_context(settings)
    payload = {
        "model": cstr(settings.model).strip() or DEFAULT_AI_MODEL,
        "store": False,
        "instructions": _build_openai_instructions(settings),
        "input": _build_openai_input(message=message, history=history, context=context),
        "text": {
            "format": {
                "type": "json_schema",
                "name": "erpnext_ai_assistant_plan",
                "strict": True,
                "schema": _response_schema(),
            }
        },
    }

    try:
        response = requests.post(
            _get_ai_responses_url(settings),
            headers={
                "Authorization": f"Bearer {_get_ai_api_key(settings)}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60,
        )
    except requests.RequestException as exc:
        frappe.throw(_("AI request failed: {0}").format(exc))

    try:
        response_data = response.json()
    except ValueError:
        response_data = {}
    if not isinstance(response_data, dict):
        response_data = {}

    if response.status_code >= 400:
        error_message = (
            response_data.get("error", {}).get("message")
            or response.reason
            or f"{_get_provider_name(settings)} request failed"
        )
        frappe.throw(_("AI request failed: {0}").format(error_message))

    content = _extract_response_text(response_data)
    if not content:
        frappe.throw(_("AI assistant returned an empty response"))

    try:
        plan = json.loads(content)
    except json.JSONDecodeError as exc:
        frappe.throw(_("AI assistant returned invalid JSON: {0}").format(exc))

    if plan.get("intent") not in SUPPORTED_INTENTS:
        plan["intent"] = "unknown"

    plan.setdefault("items", [])
    plan.setdefault("email_to", [])
    plan.setdefault("missing_fields", [])
    return plan


def execute_assistant_intent(plan, settings=None):
    settings = settings or _get_settings()
    intent = cstr(plan.get("intent")).strip() or "unknown"

    # Thu tu xu ly nay phan anh muc do "thao tac duoc" cua assistant hien tai.
    if intent == "create_sales_order_draft":
        return create_sales_order_draft(
            customer=plan.get("customer"),
            items=plan.get("items") or [],
            company=plan.get("company"),
            warehouse=plan.get("warehouse"),
            delivery_date=plan.get("delivery_date"),
            notes=plan.get("notes"),
            settings=settings,
        )

    if intent == "create_customer":
        return create_customer(
            customer=plan.get("customer"),
            customer_type=plan.get("customer_type"),
            customer_group=plan.get("customer_group"),
            territory=plan.get("territory"),
            customer_channel=plan.get("customer_channel"),
            notes=plan.get("notes"),
        )

    if intent == "create_auto_email_report":
        return create_auto_email_report(
            report_name=plan.get("report_name"),
            email_to=plan.get("email_to") or [],
            frequency=plan.get("frequency"),
            format=plan.get("format"),
            enabled=plan.get("enable_report"),
            notes=plan.get("notes"),
            requested_filters=plan.get("filters") or [],
            settings=settings,
        )

    if intent == "stock_lookup":
        return lookup_stock(
            item_query=plan.get("item_query"),
            warehouse=plan.get("warehouse"),
            company=plan.get("company"),
        )

    if intent == "erp_workflow_copilot":
        return _assistant_result(
            status="needs_input",
            reply=plan.get("assistant_message") or _default_help_text(),
            data={
                "workflow_key": plan.get("workflow_key"),
                "required_fields": plan.get("missing_fields") or [],
            },
        )

    if intent == "help":
        return _assistant_result(
            status="needs_input",
            reply=plan.get("assistant_message") or _default_help_text(),
        )

    return _assistant_result(
        status="needs_input",
        reply=plan.get("assistant_message") or _default_help_text(),
    )


def create_sales_order_draft(
    *,
    customer,
    items,
    company=None,
    warehouse=None,
    delivery_date=None,
    notes=None,
    settings=None,
):
    _ensure_permission("Sales Order", "create")
    settings = settings or _get_settings()

    if not customer:
        return _assistant_result(
            status="needs_input",
            reply="Can ten khach hang de tao don nhap.",
        )

    if not items:
        return _assistant_result(
            status="needs_input",
            reply="Can it nhat 1 mat hang va so luong de tao don nhap.",
        )

    customer_match = _resolve_customer(customer)
    if customer_match["ambiguous"]:
        return _assistant_result(
            status="needs_input",
            reply=f"Khach hang chua ro. Ban muon chon: {', '.join(customer_match['alternatives'])}?",
        )
    if not customer_match["match"]:
        return _assistant_result(
            status="needs_input",
            reply=f"Khong tim thay khach hang phu hop voi '{customer}'.",
        )

    company_name = _resolve_company(company or settings.default_company)
    if not company_name:
        return _assistant_result(
            status="error",
            reply="Khong tim thay default company trong cau hinh code cua AI Assistant.",
        )

    warehouse_match = _resolve_warehouse(warehouse or settings.default_warehouse) if (warehouse or settings.default_warehouse) else {"match": None, "ambiguous": False, "alternatives": []}
    if warehouse_match.get("ambiguous"):
        return _assistant_result(
            status="needs_input",
            reply=f"Kho chua ro. Ban muon chon: {', '.join(warehouse_match['alternatives'])}?",
        )
    if warehouse and not warehouse_match.get("match"):
        return _assistant_result(
            status="needs_input",
            reply=f"Khong tim thay kho phu hop voi '{warehouse}'.",
        )

    resolved_items = []
    for row in items:
        item_query = row.get("item_query")
        qty = flt(row.get("qty"))
        row_warehouse_query = row.get("warehouse")

        if not item_query or qty <= 0:
            return _assistant_result(
                status="needs_input",
                reply="Moi dong hang can co item va qty > 0.",
            )

        item_match = _resolve_item(item_query)
        if item_match["ambiguous"]:
            return _assistant_result(
                status="needs_input",
                reply=f"Mat hang '{item_query}' chua ro. Goi y: {', '.join(item_match['alternatives'])}.",
            )
        if not item_match["match"]:
            return _assistant_result(
                status="needs_input",
                reply=f"Khong tim thay item phu hop voi '{item_query}'.",
            )

        row_warehouse_match = warehouse_match
        if row_warehouse_query:
            row_warehouse_match = _resolve_warehouse(row_warehouse_query)
            if row_warehouse_match["ambiguous"]:
                return _assistant_result(
                    status="needs_input",
                    reply=f"Kho cho item '{item_query}' chua ro. Goi y: {', '.join(row_warehouse_match['alternatives'])}.",
                )
            if not row_warehouse_match["match"]:
                return _assistant_result(
                    status="needs_input",
                    reply=f"Khong tim thay kho phu hop voi '{row_warehouse_query}'.",
                )

        resolved_items.append(
            {
                "item_code": item_match["match"]["name"],
                "item_name": item_match["match"].get("item_name") or item_match["match"]["name"],
                "qty": qty,
                "warehouse": row_warehouse_match["match"]["name"] if row_warehouse_match.get("match") else None,
            }
        )

    order = frappe.new_doc("Sales Order")
    order.customer = customer_match["match"]["name"]
    order.company = company_name
    order.order_type = "Sales"
    order.transaction_date = nowdate()
    order.delivery_date = _coerce_date(delivery_date) or nowdate()

    default_price_list = _get_default_selling_price_list()
    company_currency = frappe.db.get_value("Company", company_name, "default_currency")

    if default_price_list:
        order.selling_price_list = default_price_list
    if company_currency:
        order.currency = company_currency
        order.price_list_currency = company_currency
        order.conversion_rate = 1
        order.plc_conversion_rate = 1
    if warehouse_match.get("match"):
        order.set_warehouse = warehouse_match["match"]["name"]

    for row in resolved_items:
        order.append(
            "items",
            {
                "item_code": row["item_code"],
                "qty": row["qty"],
                "warehouse": row["warehouse"] or order.set_warehouse,
                "delivery_date": order.delivery_date,
            },
        )

    item_warehouses = sorted({row["warehouse"] for row in resolved_items if row["warehouse"]})
    if not order.set_warehouse and len(item_warehouses) == 1:
        order.set_warehouse = item_warehouses[0]

    order.run_method("set_missing_values")
    order.run_method("calculate_taxes_and_totals")
    order.insert()

    item_summary = ", ".join(
        f"{_format_qty(row['qty'])} x {row['item_code']}" for row in resolved_items
    )
    reply = (
        f"Da tao Sales Order nhap {order.name} cho {customer_match['match'].get('customer_name') or order.customer}.\n"
        f"Hang hoa: {item_summary}."
    )
    if item_warehouses:
        reply += f"\nKho hang: {', '.join(item_warehouses)}."
    if notes:
        reply += f"\nGhi chu yeu cau: {notes}."

    return _assistant_result(
        status="completed",
        reply=reply,
        data={
            "doctype": order.doctype,
            "name": order.name,
            "docstatus": order.docstatus,
            "items": resolved_items,
        },
        primary_action=_route_action("Open Sales Order", ["Form", "Sales Order", order.name]),
    )


def create_customer(
    *,
    customer,
    customer_type=None,
    customer_group=None,
    territory=None,
    customer_channel=None,
    notes=None,
):
    _ensure_permission("Customer", "create")

    customer_name = cstr(customer).strip()
    if not customer_name:
        return _assistant_result(
            status="needs_input",
            reply="Can ten khach hang moi de tao ho so Customer.",
        )

    existing_customer = (
        frappe.db.get_value(
            "Customer",
            {"customer_name": customer_name},
            ["name", "customer_name"],
            as_dict=1,
        )
        or frappe.db.get_value(
            "Customer",
            {"name": customer_name},
            ["name", "customer_name"],
            as_dict=1,
        )
    )
    if existing_customer:
        existing_label = existing_customer.get("customer_name") or existing_customer.get("name")
        return _assistant_result(
            status="completed",
            reply=f"Khach hang {existing_label} da ton tai, khong tao moi them.",
            data={
                "doctype": "Customer",
                "name": existing_customer.get("name"),
                "customer_name": existing_label,
                "existing": True,
            },
            primary_action=_route_action(
                "Open Customer",
                ["Form", "Customer", existing_customer.get("name")],
            ),
        )

    existing_match = _resolve_customer(customer_name)
    if existing_match["ambiguous"]:
        return _assistant_result(
            status="needs_input",
            reply=f"Ten khach hang gan giong du lieu hien co. Ban muon chon: {', '.join(existing_match['alternatives'])}?",
        )

    resolved_customer_type = _normalize_customer_type(customer_type) or "Company"
    resolved_channel = _normalize_customer_channel(customer_channel)
    if customer_channel and not resolved_channel:
        return _assistant_result(
            status="needs_input",
            reply="Customer Channel chua hop le. Ban co the dung Hospital, Clinic, Pharmacy, Distributor hoac B2C.",
        )

    customer_group_match = (
        _resolve_customer_group(customer_group)
        if customer_group
        else {"match": None, "ambiguous": False, "alternatives": []}
    )
    if customer_group_match["ambiguous"]:
        return _assistant_result(
            status="needs_input",
            reply=f"Customer Group chua ro. Ban muon chon: {', '.join(customer_group_match['alternatives'])}?",
        )
    if customer_group and not customer_group_match["match"]:
        return _assistant_result(
            status="needs_input",
            reply=f"Khong tim thay Customer Group phu hop voi '{customer_group}'.",
        )

    territory_match = (
        _resolve_territory(territory)
        if territory
        else {"match": None, "ambiguous": False, "alternatives": []}
    )
    if territory_match["ambiguous"]:
        return _assistant_result(
            status="needs_input",
            reply=f"Territory chua ro. Ban muon chon: {', '.join(territory_match['alternatives'])}?",
        )
    if territory and not territory_match["match"]:
        return _assistant_result(
            status="needs_input",
            reply=f"Khong tim thay Territory phu hop voi '{territory}'.",
        )

    default_customer_group = _get_default_customer_group()
    default_territory = _get_default_territory()
    resolved_customer_group = (
        customer_group_match["match"]["name"] if customer_group_match["match"] else default_customer_group
    )
    resolved_territory = (
        territory_match["match"]["name"] if territory_match["match"] else default_territory
    )

    if not resolved_customer_group:
        return _assistant_result(
            status="error",
            reply="Khong tim thay Customer Group mac dinh de tao khach hang.",
        )

    if not resolved_territory:
        return _assistant_result(
            status="error",
            reply="Khong tim thay Territory mac dinh de tao khach hang.",
        )

    customer_doc = frappe.new_doc("Customer")
    customer_doc.customer_name = customer_name
    customer_doc.customer_type = resolved_customer_type
    customer_doc.customer_group = resolved_customer_group
    customer_doc.territory = resolved_territory
    if hasattr(customer_doc, "naming_series"):
        customer_doc.naming_series = CUSTOMER_NAMING_SERIES

    if resolved_channel and frappe.db.has_column("Customer", "customer_channel"):
        customer_doc.customer_channel = resolved_channel

    customer_doc.insert()

    if notes:
        customer_doc.add_comment("Comment", f"AI Assistant note: {notes}")

    reply_lines = [
        f"Da tao Customer {customer_doc.name} cho khach hang {customer_doc.customer_name}.",
        f"Loai: {resolved_customer_type}. Customer Group: {resolved_customer_group}. Territory: {resolved_territory}.",
    ]
    if resolved_channel:
        reply_lines.append(f"Customer Channel: {resolved_channel}.")

    return _assistant_result(
        status="completed",
        reply="\n".join(reply_lines),
        data={
            "doctype": customer_doc.doctype,
            "name": customer_doc.name,
            "customer_name": customer_doc.customer_name,
            "customer_type": resolved_customer_type,
            "customer_group": resolved_customer_group,
            "territory": resolved_territory,
            "customer_channel": resolved_channel,
        },
        primary_action=_route_action("Open Customer", ["Form", "Customer", customer_doc.name]),
    )


def create_auto_email_report(
    *,
    report_name,
    email_to=None,
    frequency=None,
    format=None,
    enabled=None,
    notes=None,
    requested_filters=None,
    settings=None,
):
    _ensure_permission("Auto Email Report", "create")
    settings = settings or _get_settings()

    if not report_name:
        return _assistant_result(
            status="needs_input",
            reply="Can ten report de tao lich gui bao cao.",
        )

    report_match = _resolve_report(report_name)
    if report_match["ambiguous"]:
        return _assistant_result(
            status="needs_input",
            reply=f"Report chua ro. Ban muon chon: {', '.join(report_match['alternatives'])}?",
        )
    if not report_match["match"]:
        return _assistant_result(
            status="needs_input",
            reply=f"Khong tim thay report phu hop voi '{report_name}'.",
        )

    recipients = _normalize_emails(email_to) or _normalize_emails(
        settings.default_report_recipients
    )
    if not recipients:
        current_user_email = _get_current_user_email()
        if current_user_email:
            recipients = [current_user_email]

    if not recipients:
        return _assistant_result(
            status="needs_input",
            reply="Can email nguoi nhan de tao Auto Email Report.",
        )

    normalized_frequency = _normalize_frequency(frequency)
    if not normalized_frequency:
        return _assistant_result(
            status="needs_input",
            reply="Can tan suat bao cao: Daily, Weekdays, Weekly hoac Monthly.",
        )

    normalized_format = _normalize_format(format) or "XLSX"
    report_doc = frappe.get_doc(
        {
            "doctype": "Auto Email Report",
            "report": report_match["match"]["name"],
            "user": frappe.session.user,
            "enabled": 1 if enabled is not False else 0,
            "email_to": "\n".join(recipients),
            "frequency": normalized_frequency,
            "format": normalized_format,
            "description": _build_report_description(notes, requested_filters),
        }
    )
    if normalized_frequency == "Weekly":
        report_doc.day_of_week = getdate(nowdate()).strftime("%A")

    report_doc.insert()

    reply = (
        f"Da tao Auto Email Report {report_doc.name} cho report {report_match['match']['name']}.\n"
        f"Tan suat: {normalized_frequency}. Dinh dang: {normalized_format}. Nguoi nhan: {', '.join(recipients)}."
    )
    if requested_filters:
        reply += "\nYeu cau filter da duoc ghi vao mo ta de review them."

    return _assistant_result(
        status="completed",
        reply=reply,
        data={
            "doctype": report_doc.doctype,
            "name": report_doc.name,
            "report": report_match["match"]["name"],
            "frequency": normalized_frequency,
            "format": normalized_format,
            "email_to": recipients,
        },
        primary_action=_route_action(
            "Open Auto Email Report",
            ["Form", "Auto Email Report", report_doc.name],
        ),
    )


def lookup_stock(*, item_query, warehouse=None, company=None):
    _ensure_permission("Item", "read")

    if not item_query:
        return _assistant_result(
            status="needs_input",
            reply="Can item code hoac ten item de kiem tra ton kho.",
        )

    item_match = _resolve_item(item_query)
    if item_match["ambiguous"]:
        return _assistant_result(
            status="needs_input",
            reply=f"Item chua ro. Goi y: {', '.join(item_match['alternatives'])}.",
        )
    if not item_match["match"]:
        return _assistant_result(
            status="needs_input",
            reply=f"Khong tim thay item phu hop voi '{item_query}'.",
        )

    warehouse_match = _resolve_warehouse(warehouse) if warehouse else {"match": None, "ambiguous": False, "alternatives": []}
    if warehouse_match.get("ambiguous"):
        return _assistant_result(
            status="needs_input",
            reply=f"Kho chua ro. Ban muon chon: {', '.join(warehouse_match['alternatives'])}?",
        )
    if warehouse and not warehouse_match.get("match"):
        return _assistant_result(
            status="needs_input",
            reply=f"Khong tim thay kho phu hop voi '{warehouse}'.",
        )

    bin_filters = {"item_code": item_match["match"]["name"]}
    if warehouse_match.get("match"):
        bin_filters["warehouse"] = warehouse_match["match"]["name"]

    bin_rows = frappe.get_all(
        "Bin",
        filters=bin_filters,
        fields=["warehouse", "actual_qty", "projected_qty", "reserved_qty", "stock_uom"],
        order_by="actual_qty desc, warehouse asc",
        limit_page_length=50,
    )

    if company:
        company_name = _resolve_company(company)
        if company_name:
            allowed_warehouses = {
                row.name
                for row in frappe.get_all(
                    "Warehouse",
                    filters={"company": company_name, "is_group": 0},
                    fields=["name"],
                    limit_page_length=0,
                )
            }
            bin_rows = [row for row in bin_rows if row.warehouse in allowed_warehouses]

    total_actual = sum(flt(row.actual_qty) for row in bin_rows)
    cell_rows = _get_cell_stock_rows(
        item_code=item_match["match"]["name"],
        warehouse=warehouse_match["match"]["name"] if warehouse_match.get("match") else None,
    )
    total_cell_qty = sum(flt(row["qty"]) for row in cell_rows)
    reported_total = total_actual if total_actual > 0 or not total_cell_qty else total_cell_qty

    if not bin_rows and not cell_rows:
        return _assistant_result(
            status="completed",
            reply=f"Khong co ton on-hand cho {item_match['match']['name']} trong pham vi da chon.",
            data={
                "item_code": item_match["match"]["name"],
                "item_name": item_match["match"].get("item_name"),
                "warehouse_rows": [],
                "cell_rows": [],
            },
            primary_action=_route_action("Open Item", ["Form", "Item", item_match["match"]["name"]]),
        )

    stock_uom = item_match["match"].get("stock_uom") or ""
    lines = [
        f"Ton kho cho {item_match['match']['name']} - {item_match['match'].get('item_name') or item_match['match']['name']}: {_format_qty(reported_total)} {stock_uom}".strip()
    ]

    cell_rows_by_warehouse = {}
    for row in cell_rows:
        cell_rows_by_warehouse.setdefault(row["warehouse"], []).append(row)

    for row in bin_rows[:10]:
        warehouse_line = (
            f"- {row.warehouse}: ton {_format_qty(row.actual_qty)}, projected {_format_qty(row.projected_qty)}, reserved {_format_qty(row.reserved_qty)}"
        )
        warehouse_cells = cell_rows_by_warehouse.get(row.warehouse) or []
        if warehouse_cells:
            cell_summary = ", ".join(
                f"{cell['cell_code']}: {_format_qty(cell['qty'])}"
                for cell in warehouse_cells[:6]
            )
            warehouse_line = f"{warehouse_line}. Vi tri 2D: {cell_summary}"
        lines.append(warehouse_line)

    extra_cell_warehouses = [
        warehouse_name
        for warehouse_name in cell_rows_by_warehouse
        if warehouse_name not in {row.warehouse for row in bin_rows}
    ]
    for warehouse_name in extra_cell_warehouses[:10]:
        warehouse_cells = cell_rows_by_warehouse[warehouse_name]
        warehouse_total = sum(flt(cell["qty"]) for cell in warehouse_cells)
        cell_summary = ", ".join(
            f"{cell['cell_code']}: {_format_qty(cell['qty'])}"
            for cell in warehouse_cells[:6]
        )
        lines.append(
            f"- {warehouse_name}: ton {_format_qty(warehouse_total)} {stock_uom}. Vi tri 2D: {cell_summary}".strip()
        )

    if cell_rows:
        if total_actual <= 0 and total_cell_qty > 0:
            lines.append("Luu y: Bin chua cap nhat kip, nhung kho 2D dang ghi nhan ton thuc te o cac vi tri tren.")

    secondary_actions = []
    unique_layouts = sorted({row["layout"] for row in cell_rows if row.get("layout")})
    if len(unique_layouts) == 1:
        secondary_actions.append(
            _route_action("Open WH Layout", ["Form", "WH Layout", unique_layouts[0]])
        )

    return _assistant_result(
        status="completed",
        reply="\n".join(lines),
        data={
            "item_code": item_match["match"]["name"],
            "item_name": item_match["match"].get("item_name"),
            "warehouse_rows": [
                {
                    "warehouse": row.warehouse,
                    "actual_qty": flt(row.actual_qty),
                    "projected_qty": flt(row.projected_qty),
                    "reserved_qty": flt(row.reserved_qty),
                    "stock_uom": row.stock_uom,
                }
                for row in bin_rows
            ],
            "cell_rows": cell_rows,
        },
        primary_action=_route_action("Open Item", ["Form", "Item", item_match["match"]["name"]]),
        secondary_actions=secondary_actions,
    )


def _build_runtime_context(settings):
    # Context nay co y o muc gon nhe, chi dua cac reference can thiet de model khong hallucinate.
    return {
        "today": nowdate(),
        "current_user": {
            "id": frappe.session.user,
            "email": _get_current_user_email(),
            "full_name": _get_current_user_full_name(),
        },
        "defaults": {
            "company": _resolve_company(settings.default_company),
            "warehouse": settings.default_warehouse,
            "report_recipients": _normalize_emails(
                settings.default_report_recipients
            ),
            "customer_group": _get_default_customer_group(),
            "territory": _get_default_territory(),
        },
        "customers": _get_customer_options(limit=12),
        "customer_groups": _get_customer_group_options(limit=12),
        "territories": _get_territory_options(limit=12),
        "customer_channels": sorted(set(CUSTOMER_CHANNEL_MAP.values())),
        "items": _get_item_options(limit=12),
        "warehouses": _get_warehouse_options(limit=12),
        "reports": _get_report_options(limit=20),
        "workflow_copilot": [
            "batch_release",
            "recall_case",
            "temperature_excursion",
            "invoice_compliance",
        ],
    }


def _build_openai_instructions(settings):
    custom_prompt = cstr(settings.system_prompt).strip()
    instructions = [
        "You are an ERPNext desk assistant for a pharma distribution team.",
        "Your job is to understand the user's Vietnamese or English request and return only JSON that matches the provided schema.",
        "Supported intents are: create_customer, create_sales_order_draft, create_auto_email_report, erp_workflow_copilot, stock_lookup, help, unknown.",
        "Use help intent for SOP, process explanation, invoice flow, warehouse operations, stock-check guidance, and Vietnam tax/legal questions.",
        "Use erp_workflow_copilot when the user wants guided execution for batch release, recall, temperature excursion, or e-invoice/VAT review.",
        "Never invent customer names, item codes, warehouses, reports, or emails. If you are unsure, leave the value null and add the missing field in missing_fields.",
        "For create_customer, capture the new customer name in customer. customer_type, customer_group, territory, and customer_channel are optional. If the user does not specify them, leave them null.",
        "For create_sales_order_draft, keep the order as draft only.",
        "For create_auto_email_report, prefer the current user's email if the user does not specify recipients.",
        "For stock_lookup, capture item_query and optional warehouse.",
        "If the user asks to check stock for a specific item or warehouse, prefer stock_lookup. If the user asks how to check stock or which report to use, prefer help.",
        "For legal or tax questions, answer at high level only, avoid inventing decree/article numbers, and remind the user to verify the latest official law, decree, and circular before compliance decisions.",
        "For help intent about ERP process, explain in ERPNext document order and mention the exact documents step by step, for example Quotation -> Sales Order -> Delivery Note -> Sales Invoice -> Payment Entry.",
        "assistant_message should be in Vietnamese, practical, and usually 2-6 short sentences.",
    ]
    skill_reference = _load_assistant_skill_reference()
    if skill_reference:
        instructions.append("Embedded ERP skill reference:\n" + skill_reference)
    if custom_prompt:
        instructions.append(f"Additional site instruction: {custom_prompt}")
    return "\n".join(instructions)


def _load_assistant_skill_reference():
    try:
        return ASSISTANT_SKILL_REFERENCE.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def _build_openai_input(*, message, history, context):
    input_messages = []
    for row in history:
        input_messages.append({"role": row["role"], "content": row["content"]})

    input_messages.append(
        {
            "role": "user",
            "content": "\n".join(
                [
                    "User request:",
                    message,
                    "",
                    "ERPNext runtime context:",
                    json.dumps(context, ensure_ascii=False),
                ]
            ),
        }
    )
    return input_messages


def _response_schema():
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "intent": {
                "type": "string",
                "enum": sorted(SUPPORTED_INTENTS),
            },
            "assistant_message": {"type": "string"},
            "customer": {"type": ["string", "null"]},
            "customer_type": {"type": ["string", "null"]},
            "customer_group": {"type": ["string", "null"]},
            "territory": {"type": ["string", "null"]},
            "customer_channel": {"type": ["string", "null"]},
            "company": {"type": ["string", "null"]},
            "warehouse": {"type": ["string", "null"]},
            "delivery_date": {"type": ["string", "null"]},
            "item_query": {"type": ["string", "null"]},
            "report_name": {"type": ["string", "null"]},
            "frequency": {"type": ["string", "null"]},
            "format": {"type": ["string", "null"]},
            "enable_report": {"type": "boolean"},
            "notes": {"type": ["string", "null"]},
            "workflow_key": {"type": ["string", "null"]},
            "missing_fields": {
                "type": "array",
                "items": {"type": "string"},
            },
            "email_to": {
                "type": "array",
                "items": {"type": "string"},
            },
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "item_query": {"type": ["string", "null"]},
                        "qty": {"type": ["number", "null"]},
                        "warehouse": {"type": ["string", "null"]},
                    },
                    "required": ["item_query", "qty", "warehouse"],
                },
            },
            "filters": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "fieldname": {"type": "string"},
                        "value": {"type": "string"},
                    },
                    "required": ["fieldname", "value"],
                },
            },
        },
        "required": [
            "intent",
            "assistant_message",
            "customer",
            "customer_type",
            "customer_group",
            "territory",
            "customer_channel",
            "company",
            "warehouse",
            "delivery_date",
            "item_query",
            "report_name",
            "frequency",
            "format",
            "enable_report",
            "notes",
            "workflow_key",
            "missing_fields",
            "email_to",
            "items",
            "filters",
        ],
    }


def _extract_response_text(payload):
    output_text = payload.get("output_text")
    if output_text:
        return output_text

    parts = []
    for output in payload.get("output", []):
        for content in output.get("content", []):
            text_value = content.get("text")
            if text_value:
                parts.append(text_value)

    return "\n".join(parts).strip()


def _sanitize_history(history):
    sanitized_rows = []
    for row in history[-8:]:
        role = cstr(row.get("role")).strip().lower()
        content = cstr(row.get("content")).strip()
        if role not in {"user", "assistant"} or not content:
            continue
        sanitized_rows.append({"role": role, "content": content})
    return sanitized_rows


def _assistant_result(status, reply, data=None, primary_action=None, secondary_actions=None, bootstrap=None):
    return {
        "status": status,
        "reply": reply,
        "data": data or {},
        "primary_action": primary_action,
        "secondary_actions": secondary_actions or [],
        "bootstrap": bootstrap or {},
    }


def _route_action(label, route):
    return {
        "label": label,
        "route": route,
    }


def _ensure_permission(doctype, ptype):
    if not frappe.has_permission(doctype=doctype, ptype=ptype):
        frappe.throw(_("You do not have permission to {0} {1}").format(ptype, doctype))


def _get_settings():
    return frappe._dict(
        {
            "enabled": assistant_config.ENABLED,
            "api_key": assistant_config.API_KEY,
            "api_base_url": assistant_config.API_BASE_URL,
            "provider_name": assistant_config.PROVIDER_NAME,
            "api_key_env_var": assistant_config.API_KEY_ENV_VAR,
            "model": assistant_config.MODEL,
            "default_company": assistant_config.DEFAULT_COMPANY,
            "default_warehouse": assistant_config.DEFAULT_WAREHOUSE,
            "default_report_recipients": assistant_config.DEFAULT_REPORT_RECIPIENTS,
            "system_prompt": assistant_config.SYSTEM_PROMPT,
        }
    )


def _get_ai_api_key(settings):
    return cstr(settings.api_key).strip()


def _get_ai_base_url(settings):
    return cstr(settings.api_base_url).strip().rstrip("/") or assistant_config.API_BASE_URL


def _get_ai_responses_url(settings):
    return f"{_get_ai_base_url(settings)}/responses"


def _get_provider_name(settings):
    return cstr(settings.provider_name).strip() or "AI"


def _get_api_key_env_var(settings):
    return cstr(settings.api_key_env_var).strip() or "OPENAI_API_KEY"


def _get_current_user_email():
    return frappe.db.get_value("User", frappe.session.user, "email")


def _get_current_user_full_name():
    return cstr(frappe.db.get_value("User", frappe.session.user, "full_name")).strip()


def _get_current_user_label():
    return (
        _get_current_user_full_name()
        or cstr(getattr(frappe.session, "user_fullname", "")).strip()
        or cstr(frappe.session.user).strip()
        or _get_current_user_email()
        or "Ban"
    )


def _build_local_help_plan(message):
    normalized = _normalize_text(message)
    if not normalized:
        return None

    asks_for_process = any(
        token in normalized
        for token in (
            "quy trinh",
            "quy trinh nao",
            "nhu the nao",
            "nhu nao",
            "cach lam",
            "cach len",
            "khi nao dung",
            "nen dung chung tu nao",
            "giai thich",
        )
    )
    explicit_action = any(
        token in normalized
        for token in (
            "create ",
            "tao ",
            "lap ",
            "check stock for",
            "kiem tra ton kho cho",
            "draft ",
            "schedule ",
        )
    )
    if explicit_action and not asks_for_process:
        return None

    if asks_for_process:
        if _has_sales_process_signal(normalized):
            best_topic = "sales_flow"
        elif _has_purchase_process_signal(normalized):
            best_topic = "purchase_flow"
        elif _has_transfer_signal(normalized):
            best_topic = "inventory_transfer"
        elif _has_receipt_signal(normalized):
            best_topic = "inventory_receipt"
        elif _has_issue_signal(normalized):
            best_topic = "inventory_issue"
        elif _has_invoice_signal(normalized):
            best_topic = "invoice_flow"
        elif _has_stock_signal(normalized):
            best_topic = "stock_check"
        elif _has_legal_signal(normalized):
            best_topic = "legal_guidance"
        else:
            best_topic = None
        if best_topic:
            return {
                "intent": "help",
                "assistant_message": _build_help_reply(best_topic),
                "customer": None,
                "customer_type": None,
                "customer_group": None,
                "territory": None,
                "customer_channel": None,
                "company": None,
                "warehouse": None,
                "delivery_date": None,
                "item_query": None,
                "report_name": None,
                "frequency": None,
                "format": None,
                "enable_report": False,
                "notes": None,
                "workflow_key": None,
                "missing_fields": [],
                "email_to": [],
                "items": [],
                "filters": [],
            }

    best_topic = None
    best_score = 0
    for row in LOCAL_HELP_PATTERNS:
        score = sum(1 for keyword in row["keywords"] if keyword in normalized)
        if score > best_score:
            best_score = score
            best_topic = row["topic"]

    if not best_topic:
        return None

    return {
        "intent": "help",
        "assistant_message": _build_help_reply(best_topic),
        "customer": None,
        "customer_type": None,
        "customer_group": None,
        "territory": None,
        "customer_channel": None,
        "company": None,
        "warehouse": None,
        "delivery_date": None,
        "item_query": None,
        "report_name": None,
        "frequency": None,
        "format": None,
        "enable_report": False,
        "notes": None,
        "workflow_key": None,
        "missing_fields": [],
        "email_to": [],
        "items": [],
        "filters": [],
    }


def _build_local_stock_lookup_plan(message):
    raw_message = cstr(message).strip()
    normalized = _normalize_text(message)
    if not raw_message or not normalized:
        return None

    patterns = [
        r"^(?:check stock for|check stock|stock check|stock checks)\s+(.+)$",
        r"^(?:kiem tra ton kho cho|kiem tra ton kho|xem ton kho)\s+(.+)$",
    ]

    matched_query = None
    for pattern in patterns:
        match = re.match(pattern, normalized)
        if match:
            matched_query = cstr(match.group(1)).strip()
            break

    item_query = None
    warehouse = None
    search_text = matched_query or raw_message

    if matched_query:
        item_query, warehouse = _split_item_and_warehouse(search_text)
    elif _has_stock_signal(normalized):
        item_query, warehouse = _extract_stock_targets(raw_message, normalized)

    if not item_query:
        return None

    return {
        "intent": "stock_lookup",
        "assistant_message": "",
        "customer": None,
        "customer_type": None,
        "customer_group": None,
        "territory": None,
        "customer_channel": None,
        "company": None,
        "warehouse": warehouse,
        "delivery_date": None,
        "item_query": item_query,
        "report_name": None,
        "frequency": None,
        "format": None,
        "enable_report": None,
        "email_to": [],
        "filters": [],
        "notes": None,
        "items": [],
        "missing_fields": [],
    }


def _split_item_and_warehouse(text):
    text = cstr(text).strip()
    if not text:
        return None, None

    warehouse = None
    item_query = text

    warehouse_match = re.match(r"(.+?)\s+(?:in|tai|o)\s+(.+)$", _normalize_text(text))
    if warehouse_match:
        source_match = re.match(r"(.+?)\s+(?:in|tai|o)\s+(.+)$", text, flags=re.IGNORECASE)
        if source_match:
            item_query = cstr(source_match.group(1)).strip(" ,.:;?-")
            warehouse = cstr(source_match.group(2)).strip(" ,.:;?-")

    if item_query:
        item_query = _clean_stock_subject(item_query)
    if warehouse:
        warehouse = _clean_stock_warehouse(warehouse)
    return item_query or None, warehouse or None


def _extract_stock_targets(raw_message, normalized_message):
    working_text = cstr(raw_message).strip()
    normalized = cstr(normalized_message).strip()
    if not working_text or not normalized:
        return None, None

    warehouse, working_text, normalized = _extract_warehouse_hint(working_text, normalized)

    item_code = _extract_item_code(working_text) or _extract_item_code(normalized)
    if item_code:
        return item_code, _clean_stock_warehouse(warehouse)

    item_query = _clean_stock_subject(working_text)
    if not item_query:
        return None, _clean_stock_warehouse(warehouse)

    tokens = [token for token in _normalize_text(item_query).split() if token]
    if len(tokens) < 2 and not re.search(r"\d", item_query):
        return None, _clean_stock_warehouse(warehouse)

    return item_query, _clean_stock_warehouse(warehouse)


def _extract_warehouse_hint(raw_message, normalized_message):
    raw_text = cstr(raw_message).strip()
    normalized = cstr(normalized_message).strip()
    if not raw_text or not normalized:
        return None, raw_text, normalized

    patterns = (
        r"\b(?:tai|o|in)\s+kho\s+(.+)$",
        r"\btrong\s+kho\s+(.+)$",
        r"\bwarehouse\s+(.+)$",
        r"\b(?:tai|o|in)\s+([a-z0-9][a-z0-9 \-_/().]+)$",
    )

    for pattern in patterns:
        normalized_match = re.search(pattern, normalized)
        if not normalized_match:
            continue

        source_match = re.search(pattern, raw_text, flags=re.IGNORECASE)
        warehouse = cstr(
            source_match.group(1) if source_match else normalized_match.group(1)
        ).strip(" ,.:;?-")
        trimmed_raw = raw_text[: source_match.start()].strip() if source_match else raw_text
        trimmed_normalized = normalized[: normalized_match.start()].strip()
        return warehouse, trimmed_raw, trimmed_normalized

    return None, raw_text, normalized


def _extract_item_code(text):
    value = cstr(text).strip()
    if not value:
        return None

    for pattern in (
        r"\b[A-Z]{1,12}-\d{2,}\b",
        r"\b[A-Z0-9]{2,12}-[A-Z0-9]{1,12}\b",
        r"\b[A-Z]{2,12}\d{2,}\b",
    ):
        match = re.search(pattern, value)
        if match:
            return cstr(match.group(0)).strip()
    return None


def _clean_stock_subject(text):
    value = cstr(text).strip()
    if not value:
        return ""

    patterns = [
        r"^(?:check|kiem tra|xem|co the xem|show|tra cuu)\s+",
        r"^(?:ton kho|stock|stock check|stock checks)\s+",
        r"^(?:mat hang|ma hang|hang hoa|hang|item|san pham)\s+",
        r"^(?:cua|cho)\s+",
    ]
    previous = None
    while value and value != previous:
        previous = value
        for pattern in patterns:
            value = re.sub(pattern, "", value, count=1, flags=re.IGNORECASE).strip()

    value = re.sub(
        r"\b(?:ton kho|stock|con hang khong|con bao nhieu|bao nhieu|giup toi|dum|dum toi|voi|nhe)\b",
        " ",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(r"\s+", " ", value).strip(" ,.:;?-")
    return value


def _clean_stock_warehouse(text):
    value = cstr(text).strip()
    if not value:
        return ""

    value = re.sub(r"\b(?:nay|do|nay nhe|nhe|voi)\b", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"\s+", " ", value).strip(" ,.:;?-")
    return value


def _build_local_copilot_plan(message):
    workflow_key = detect_copilot_workflow(message)
    if not workflow_key:
        return None

    # Copilot local hien la mode huong dan quy trinh; chua tu dong thuc thi tac vu nhay cam.
    return {
        "intent": "erp_workflow_copilot",
        "assistant_message": build_copilot_reply(workflow_key),
        "customer": None,
        "customer_type": None,
        "customer_group": None,
        "territory": None,
        "customer_channel": None,
        "company": None,
        "warehouse": None,
        "delivery_date": None,
        "item_query": None,
        "report_name": None,
        "frequency": None,
        "format": None,
        "enable_report": False,
        "notes": None,
        "workflow_key": workflow_key,
        "missing_fields": [],
        "email_to": [],
        "items": [],
        "filters": [],
    }


def _build_help_reply(topic):
    replies = {
        "sales_flow": (
            "Quy trinh len don ban hang trong ERPNext nen di theo thu tu: Bao gia `Quotation` -> Don ban `Sales Order` -> Phieu xuat `Delivery Note` -> Hoa don `Sales Invoice` -> Thu tien `Payment Entry`.\n"
            "Buoc 1: vao `Selling > Quotation`, tao bao gia neu can bao gia truoc.\n"
            "Buoc 2: tu bao gia tao `Sales Order`, nhap khach hang, ngay giao, item, so luong, kho xuat roi `Submit`.\n"
            "Buoc 3: tu `Sales Order` tao `Delivery Note`, chon batch theo FEFO va kiem tra ton thuc te trong kho `Released`.\n"
            "Buoc 4: submit `Delivery Note` de tru ton kho.\n"
            "Buoc 5: tu `Delivery Note` tao `Sales Invoice`, kiem tra gia ban va VAT roi submit.\n"
            "Buoc 6: neu da thu tien thi tao `Payment Entry`.\n"
            "Neu ban nhanh khong can bao gia, co the bat dau tu `Sales Order`."
        ),
        "purchase_flow": (
            "Quy trinh mua hang trong ERPNext nen di theo thu tu: `Purchase Order` -> `Purchase Receipt` -> `Purchase Invoice` -> `Payment Entry`.\n"
            "Buoc 1: vao `Buying > Purchase Order`, nhap nha cung cap, kho nhap, item, so luong, gia mua roi submit.\n"
            "Buoc 2: khi hang ve, tu PO tao `Purchase Receipt` de nhap kho.\n"
            "Buoc 3: neu hang can QA thi nhap vao kho `Quarantine`, gan batch va submit phieu nhap.\n"
            "Buoc 4: QA release xong moi chuyen sang kho `Released`.\n"
            "Buoc 5: ke toan tao `Purchase Invoice` va sau do thanh toan bang `Payment Entry`."
        ),
        "inventory_issue": (
            "Neu la xuat kho noi bo, khong giao cho khach hang, nen dung `Stock Entry` voi purpose `Material Issue`.\n"
            "Buoc 1: vao `Stock > Stock Entry`.\n"
            "Buoc 2: chon purpose `Material Issue`.\n"
            "Buoc 3: nhap `s_warehouse`, item, so luong, batch neu co.\n"
            "Buoc 4: save va submit de tru ton.\n"
            "Neu la xuat cho khach hang thi khong dung `Material Issue`, ma dung `Sales Order -> Delivery Note`."
        ),
        "inventory_receipt": (
            "Neu la nhap kho noi bo, khong di qua mua hang, nen dung `Stock Entry` voi purpose `Material Receipt`.\n"
            "Buoc 1: vao `Stock > Stock Entry`.\n"
            "Buoc 2: chon purpose `Material Receipt`.\n"
            "Buoc 3: nhap `t_warehouse`, item, so luong, batch neu can.\n"
            "Buoc 4: save va submit de tang ton kho.\n"
            "Neu nhap tu nha cung cap thi nen dung `Purchase Order -> Purchase Receipt`."
        ),
        "inventory_transfer": (
            "Chuyen kho trong ERPNext nen dung `Stock Entry` voi purpose `Material Transfer`.\n"
            "Buoc 1: vao `Stock > Stock Entry`.\n"
            "Buoc 2: chon purpose `Material Transfer`.\n"
            "Buoc 3: nhap `s_warehouse`, `t_warehouse`, item, so luong va batch.\n"
            "Buoc 4: save va submit.\n"
            "Neu la chuyen tu `Quarantine` sang `Released` sau QA thi van dung `Material Transfer`."
        ),
        "invoice_flow": (
            "Trong ERPNext, hoa don ban hang thuong di sau `Delivery Note`, con hoa don mua hang thuong di sau `Purchase Receipt`.\n"
            "Ban hang: `Sales Order -> Delivery Note -> Sales Invoice -> Payment Entry`.\n"
            "Mua hang: `Purchase Order -> Purchase Receipt -> Purchase Invoice -> Payment Entry`.\n"
            "Neu doanh nghiep co tich hop hoa don dien tu, so hoa don thuong duoc phat hanh sau khi `Sales Invoice` da submit.\n"
            "Neu ban muon, minh co the giai thich rieng quy trinh `Sales Invoice` hoac `Purchase Invoice` tung buoc."
        ),
        "stock_check": (
            "De kiem tra ton kho trong ERPNext, co 4 cach chinh.\n"
            "1. `Stock Balance`: xem ton theo item va kho.\n"
            "2. `Warehouse Wise Stock Balance`: xem ton theo tung kho.\n"
            "3. `Batch-wise Balance History`: xem ton theo lo/han dung.\n"
            "4. `Stock Ledger`: xem lich su tang giam ton.\n"
            "Neu ban muon kiem nhanh ngay trong AI Assistant, hay nhap theo mau: `Check stock for ITEM in WAREHOUSE`.\n"
            "Khi xem ton de xuat hang, nen kiem tra ton trong kho `Released`, khong phai `Quarantine`."
        ),
        "legal_guidance": (
            "Neu cau hoi lien quan `luat`, `nghi dinh`, `thong tu`, `VAT` hay hoa don dien tu, minh se giai thich theo nghiep vu ERP truoc.\n"
            "Tuy nhien phan ap dung phap ly/thue can doi chieu van ban moi nhat va xac nhan voi ke toan hoac tax advisor truoc khi van hanh.\n"
            "Trong repo hien dang co logic thue `0%`, `5%`, `8%`, `10%`, nhung khong nen tu dong gan cho moi mat hang neu chua co finance review.\n"
            "Neu ban gui ten van ban cu the, minh co the giup tom tat theo goc nhin quy trinh ERP."
        ),
    }
    return replies.get(topic, _default_help_text())


def _contains_any(text, keywords):
    return any(keyword in text for keyword in keywords)


def _has_sales_process_signal(text):
    return _contains_any(text, ("ban hang", "don hang ban", "sales order", "quotation", "bao gia")) or (
        "don hang" in text and _contains_any(text, ("khach", "khach hang", "ban"))
    )


def _has_purchase_process_signal(text):
    return _contains_any(text, ("mua hang", "purchase order", "purchase receipt", "purchase invoice", "nha cung cap"))


def _has_transfer_signal(text):
    return _contains_any(text, ("chuyen kho", "material transfer", "quarantine", "released"))


def _has_receipt_signal(text):
    return _contains_any(text, ("nhap kho", "material receipt", "nhap hang noi bo"))


def _has_issue_signal(text):
    return _contains_any(text, ("xuat kho", "xuat hang", "material issue"))


def _has_invoice_signal(text):
    return _contains_any(text, ("hoa don", "invoice", "e-invoice", "hoa don dien tu"))


def _has_stock_signal(text):
    return _contains_any(
        text,
        (
            "ton kho",
            "check stock",
            "stock check",
            "stock checks",
            "stock balance",
            "stock ledger",
            "warehouse wise stock balance",
            "con hang khong",
            "con bao nhieu",
        ),
    )


def _has_legal_signal(text):
    return _contains_any(text, ("nghi dinh", "thong tu", "luat", "vat", "thue", "phap ly"))


def _resolve_company(company):
    if company and frappe.db.exists("Company", company):
        return company

    user_default = frappe.defaults.get_user_default("Company")
    if user_default and frappe.db.exists("Company", user_default):
        return user_default

    global_default = frappe.db.get_single_value("Global Defaults", "default_company")
    if global_default and frappe.db.exists("Company", global_default):
        return global_default

    first_company = frappe.get_all("Company", fields=["name"], limit_page_length=1)
    return first_company[0].name if first_company else None


def _get_default_selling_price_list():
    value = frappe.db.get_single_value("Selling Settings", "selling_price_list")
    if value:
        return value

    rows = frappe.get_all(
        "Price List",
        filters={"selling": 1, "enabled": 1},
        fields=["name"],
        order_by="name asc",
        limit_page_length=1,
    )
    return rows[0].name if rows else None


def _resolve_item(query):
    return _resolve_reference(
        doctype="Item",
        query=query,
        fields=["name", "item_name", "stock_uom"],
        search_fields=["name", "item_name"],
        base_filters={"disabled": 0},
    )


def _resolve_customer(query):
    return _resolve_reference(
        doctype="Customer",
        query=query,
        fields=["name", "customer_name"],
        search_fields=["name", "customer_name"],
    )


def _resolve_customer_group(query):
    return _resolve_reference(
        doctype="Customer Group",
        query=query,
        fields=["name"],
        search_fields=["name"],
        base_filters={"is_group": 0},
    )


def _resolve_territory(query):
    return _resolve_reference(
        doctype="Territory",
        query=query,
        fields=["name"],
        search_fields=["name"],
        base_filters={"is_group": 0},
    )


def _resolve_warehouse(query):
    return _resolve_reference(
        doctype="Warehouse",
        query=query,
        fields=["name", "company"],
        search_fields=["name"],
        base_filters={"is_group": 0},
    )


def _resolve_report(query):
    return _resolve_reference(
        doctype="Report",
        query=query,
        fields=["name", "report_name", "ref_doctype", "report_type"],
        search_fields=["name", "report_name"],
    )


def _resolve_reference(*, doctype, query, fields, search_fields, base_filters=None):
    query = cstr(query).strip()
    if not query:
        return {"match": None, "ambiguous": False, "alternatives": []}

    base_filters = base_filters or {}
    candidates = {}

    for fieldname in search_fields:
        exact_filters = dict(base_filters)
        exact_filters[fieldname] = query
        for row in frappe.get_all(doctype, filters=exact_filters, fields=fields, limit_page_length=5):
            candidates[row.name] = row

    like_pattern = f"%{query}%"
    for row in frappe.get_all(
        doctype,
        filters=base_filters,
        or_filters=[[fieldname, "like", like_pattern] for fieldname in search_fields],
        fields=fields,
        limit_page_length=12,
    ):
        candidates[row.name] = row

    ranked = []
    for row in candidates.values():
        score = _score_candidate(query, [row.get(fieldname) for fieldname in search_fields])
        ranked.append((score, row))

    primary_label_field = search_fields[1] if len(search_fields) > 1 else search_fields[0]

    ranked.sort(
        key=lambda value: (
            value[0],
            cstr(value[1].get(primary_label_field) or value[1].name).lower(),
            cstr(value[1].name).lower(),
        ),
        reverse=True,
    )

    if not ranked:
        return {"match": None, "ambiguous": False, "alternatives": []}

    best_score, best_row = ranked[0]
    alternatives = [
        row.get(primary_label_field) or row.name
        for _, row in ranked[:3]
    ]
    ambiguous = len(ranked) > 1 and best_score < 95 and (best_score - ranked[1][0]) <= 8
    return {
        "match": best_row if best_score > 0 else None,
        "ambiguous": ambiguous,
        "alternatives": alternatives,
    }


def _score_candidate(query, values):
    normalized_query = _normalize_text(query)
    if not normalized_query:
        return 0

    best_score = 0
    for value in values:
        normalized_value = _normalize_text(value)
        if not normalized_value:
            continue
        if normalized_value == normalized_query:
            best_score = max(best_score, 100)
        elif normalized_value.startswith(normalized_query):
            best_score = max(best_score, 82)
        elif normalized_query in normalized_value:
            best_score = max(best_score, 68)
        elif all(token in normalized_value for token in normalized_query.split()):
            best_score = max(best_score, 55)
    return best_score


def _normalize_text(value):
    text = unicodedata.normalize("NFKD", cstr(value))
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def _normalize_emails(values):
    if isinstance(values, str):
        values = re.split(r"[,\n;]+", values)

    cleaned = []
    for value in values or []:
        email = cstr(value).strip()
        if email and re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            cleaned.append(email)
    return cleaned


def _normalize_customer_type(value):
    normalized_value = _normalize_text(value)
    return CUSTOMER_TYPE_MAP.get(normalized_value)


def _normalize_customer_channel(value):
    normalized_value = _normalize_text(value)
    return CUSTOMER_CHANNEL_MAP.get(normalized_value)


def _first_email_from_defaults(settings):
    emails = _normalize_emails(settings.default_report_recipients)
    return emails[0] if emails else None


def _normalize_frequency(value):
    normalized_value = _normalize_text(value)
    return REPORT_FREQUENCY_MAP.get(normalized_value)


def _normalize_format(value):
    normalized_value = _normalize_text(value)
    return REPORT_FORMAT_MAP.get(normalized_value)


def _coerce_date(value):
    if not value:
        return None

    try:
        return getdate(value).isoformat()
    except Exception:
        return None


def _build_report_description(notes, requested_filters):
    description_parts = ["Created by AI Assistant."]
    if notes:
        description_parts.append(f"Note: {notes}")
    if requested_filters:
        description_parts.append(
            "Requested filters: "
            + ", ".join(
                f"{row.get('fieldname')}: {row.get('value')}" for row in requested_filters
            )
        )
    return "\n".join(description_parts)


def _default_help_text():
    return (
        "Ban co the hoi quy trinh ban hang, mua hang, nhap xuat chuyen kho, hoa don, cach kiem tra ton kho, "
        "hoac yeu cau tao khach hang, tao Sales Order nhap, tao lich gui Auto Email Report."
    )


def _format_qty(value):
    value = flt(value)
    if abs(value - round(value)) < 0.0001:
        return str(int(round(value)))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _get_customer_options(limit=10):
    rows = frappe.get_all(
        "Customer",
        fields=["name", "customer_name"],
        order_by="modified desc",
        limit_page_length=limit,
    )
    return [{"name": row.name, "label": row.customer_name or row.name} for row in rows]


def _get_customer_group_options(limit=10):
    rows = frappe.get_all(
        "Customer Group",
        filters={"is_group": 0},
        fields=["name"],
        order_by="modified desc",
        limit_page_length=limit,
    )
    return [{"name": row.name, "label": row.name} for row in rows]


def _get_territory_options(limit=10):
    rows = frappe.get_all(
        "Territory",
        filters={"is_group": 0},
        fields=["name"],
        order_by="modified desc",
        limit_page_length=limit,
    )
    return [{"name": row.name, "label": row.name} for row in rows]


def _get_item_options(limit=10):
    rows = frappe.get_all(
        "Item",
        filters={"disabled": 0},
        fields=["name", "item_name"],
        order_by="modified desc",
        limit_page_length=limit,
    )
    return [{"name": row.name, "label": row.item_name or row.name} for row in rows]


def _get_warehouse_options(limit=10):
    rows = frappe.get_all(
        "Warehouse",
        filters={"is_group": 0},
        fields=["name"],
        order_by="modified desc",
        limit_page_length=limit,
    )
    return [{"name": row.name} for row in rows]


def _get_report_options(limit=20):
    rows = frappe.get_all(
        "Report",
        fields=["name", "report_name"],
        order_by="modified desc",
        limit_page_length=limit,
    )
    return [{"name": row.name, "label": row.report_name or row.name} for row in rows]


def _get_default_customer_group():
    user_default = frappe.defaults.get_user_default("Customer Group")
    if user_default and frappe.db.exists("Customer Group", {"name": user_default, "is_group": 0}):
        return user_default

    for preferred in ("Commercial", "Individual"):
        if frappe.db.exists("Customer Group", {"name": preferred, "is_group": 0}):
            return preferred

    rows = frappe.get_all(
        "Customer Group",
        filters={"is_group": 0},
        fields=["name"],
        order_by="name asc",
        limit_page_length=1,
    )
    return rows[0].name if rows else None


def _get_default_territory():
    user_default = frappe.defaults.get_user_default("Territory")
    if user_default and frappe.db.exists("Territory", {"name": user_default, "is_group": 0}):
        return user_default

    for preferred in ("Vietnam", "Rest Of The World"):
        if frappe.db.exists("Territory", {"name": preferred, "is_group": 0}):
            return preferred

    rows = frappe.get_all(
        "Territory",
        filters={"is_group": 0},
        fields=["name"],
        order_by="name asc",
        limit_page_length=1,
    )
    return rows[0].name if rows else None


def _get_cell_stock_rows(*, item_code, warehouse=None):
    filters = {"item_code": item_code, "qty": (">", 0)}
    if warehouse:
        filters["warehouse"] = warehouse

    stock_rows = frappe.get_all(
        "WH Cell Stock",
        filters=filters,
        fields=["layout", "warehouse", "cell", "qty", "uom", "batch_no"],
        order_by="warehouse asc, cell asc",
        limit_page_length=20,
    )
    if not stock_rows:
        return []

    cell_map = {
        row.name: row
        for row in frappe.get_all(
            "WH Cell",
            filters={"name": ["in", [row.cell for row in stock_rows]]},
            fields=["name", "cell_code", "cell_label"],
            limit_page_length=0,
        )
    }

    return [
        {
            "layout": row.layout,
            "warehouse": row.warehouse,
            "cell": row.cell,
            "cell_code": cell_map.get(row.cell).cell_code if cell_map.get(row.cell) else row.cell,
            "cell_label": cell_map.get(row.cell).cell_label if cell_map.get(row.cell) else None,
            "qty": flt(row.qty),
            "uom": row.uom,
            "batch_no": row.batch_no,
        }
        for row in stock_rows
    ]

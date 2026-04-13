import json
from pathlib import Path

import frappe
import requests
from frappe import _
from frappe.utils import cint, cstr, flt

from pharma_vn.utils.response import ok
from pharma_vn.utils.validation import get_json_payload
from pharma_vn.warehouse_layout_2d.service import build_bridge_layout_payload, get_layout_overview


DEFAULT_WCS_BRIDGE_URL = "http://127.0.0.1:5057"
DEFAULT_WCS_BRIDGE_API_KEY = "change-this-api-key"


@frappe.whitelist()
def get_layout(layout_name=None):
    layout_name = layout_name or frappe.form_dict.get("layout_name")
    if not layout_name:
        frappe.throw(_("layout_name is required"))

    return ok(_("Warehouse layout loaded"), get_layout_overview(layout_name))


@frappe.whitelist()
def get_active_layouts(warehouses=None):
    warehouses = warehouses or frappe.form_dict.get("warehouses") or []
    if isinstance(warehouses, str):
        try:
            warehouses = json.loads(warehouses)
        except json.JSONDecodeError:
            warehouses = [warehouse.strip() for warehouse in warehouses.split(",") if warehouse.strip()]

    warehouses = [warehouse for warehouse in warehouses if warehouse]
    if not warehouses:
        return ok(_("No warehouses provided"), {"layouts_by_warehouse": {}})

    layout_rows = frappe.get_all(
        "WH Layout",
        filters={
            "warehouse": ["in", warehouses],
            "is_active": 1,
        },
        fields=["name", "layout_name", "warehouse"],
        order_by="modified desc",
        limit_page_length=0,
    )

    layouts_by_warehouse = {}
    for row in layout_rows:
        if row.warehouse not in layouts_by_warehouse:
            layouts_by_warehouse[row.warehouse] = {
                "name": row.name,
                "layout_name": row.layout_name,
                "warehouse": row.warehouse,
            }

    return ok(_("Active warehouse layouts loaded"), {"layouts_by_warehouse": layouts_by_warehouse})


@frappe.whitelist()
def connect_plc_simulator(layout_name=None, payload=None):
    data = get_json_payload(payload)
    layout_name = layout_name or data.get("layout_name") or frappe.form_dict.get("layout_name")
    if not layout_name:
        frappe.throw(_("layout_name is required"))

    layout_doc = frappe.get_doc("WH Layout", layout_name)

    bridge_url = _normalize_bridge_url(
        data.get("bridge_url") or getattr(layout_doc, "wcs_bridge_url", None) or DEFAULT_WCS_BRIDGE_URL
    )
    api_key = cstr(
        data.get("api_key") or getattr(layout_doc, "wcs_bridge_api_key", None) or DEFAULT_WCS_BRIDGE_API_KEY
    ).strip()
    configuration_path = cstr(
        data.get("configuration_path") or getattr(layout_doc, "plc_gateway_configuration_path", None)
    ).strip()
    configuration_json = cstr(
        data.get("configuration_json") or getattr(layout_doc, "plc_gateway_configuration_json", None)
    ).strip()
    use_local_simulator_profile = bool(cint(data.get("use_local_simulator_profile")))
    if use_local_simulator_profile and not configuration_path and not configuration_json:
        configuration_path = _get_local_simulator_configuration_path()

    activate_all_devices = bool(
        cint(
            data.get("activate_all_devices")
            if "activate_all_devices" in data
            else getattr(layout_doc, "activate_all_devices_on_connect", 1)
        )
    )
    headers = {"X-API-Key": api_key}
    generated_layout = build_bridge_layout_payload(layout_doc)
    layout_json = json.dumps(generated_layout)
    actions = []
    notices = []

    health = _bridge_request("GET", f"{bridge_url}/health", timeout=5)
    initialized_before_connect = bool(health.get("initialized"))

    if initialized_before_connect:
        if configuration_path or configuration_json:
            notices.append(
                _(
                    "Bridge da duoc initialize truoc do, nen gateway configuration moi chua duoc ap dung. Hay restart wcs-bridge-api neu muon doi simulator/PLC config."
                )
            )

        _bridge_request(
            "POST",
            f"{bridge_url}/api/gateway/layout",
            headers=headers,
            json_payload={"layoutJson": layout_json},
            timeout=30,
        )
        actions.append("layout_loaded")

        if activate_all_devices:
            _bridge_request(
                "POST",
                f"{bridge_url}/api/gateway/devices/activate-all",
                headers=headers,
                timeout=30,
            )
            actions.append("devices_activated")
    else:
        if not configuration_path and not configuration_json:
            frappe.throw(
                _(
                    "Vui long nhap Gateway Configuration Path hoac Gateway Configuration JSON truoc khi ket noi PLC simulator."
                )
            )

        initialize_payload = {
            "activateAllDevices": activate_all_devices,
            "warehouseLayoutJson": layout_json,
        }
        if configuration_path:
            initialize_payload["configurationPath"] = configuration_path
        if configuration_json:
            initialize_payload["configurationJson"] = configuration_json

        _bridge_request(
            "POST",
            f"{bridge_url}/api/gateway/initialize",
            headers=headers,
            json_payload=initialize_payload,
            timeout=30,
        )
        actions.append("gateway_initialized")
        if activate_all_devices:
            actions.append("devices_activated")

    snapshot = _bridge_request("GET", f"{bridge_url}/api/gateway/state", headers=headers, timeout=15)
    device_statuses = _bridge_request(
        "GET",
        f"{bridge_url}/api/gateway/devices/status",
        headers=headers,
        timeout=15,
    )
    devices = _bridge_request("GET", f"{bridge_url}/api/gateway/devices", headers=headers, timeout=15)

    return ok(
        _("PLC simulator connected"),
        {
            "layout_name": layout_doc.name,
            "bridge_url": bridge_url,
            "initialized_before_connect": initialized_before_connect,
            "actions": actions,
            "notices": notices,
            "snapshot": snapshot,
            "device_statuses": device_statuses,
            "devices": devices,
            "generated_layout": generated_layout,
            "used_configuration_path": configuration_path,
            "used_local_simulator_profile": use_local_simulator_profile,
        },
    )


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def search_pickable_cells(doctype, txt, searchfield, start, page_len, filters):
    filters = filters or {}
    warehouse = filters.get("warehouse")
    layout = filters.get("layout")
    item_code = filters.get("item_code")
    required_qty = flt(filters.get("required_qty"))
    batch_no = filters.get("batch_no")

    if not warehouse or not item_code:
        return []

    cell_filters = {"warehouse": warehouse, "status": ["!=", "Blocked"]}
    if layout:
        cell_filters["layout"] = layout

    cells = frappe.get_all(
        "WH Cell",
        filters=cell_filters,
        fields=["name", "cell_code", "cell_label", "layout", "warehouse", "floor", "rail", "block", "depth"],
        limit_page_length=0,
        order_by="cell_code asc, name asc",
    )
    if not cells:
        return []

    search_text = (txt or "").strip().lower()
    results = []
    for cell in cells:
        stock_filters = {
            "warehouse": warehouse,
            "cell": cell.name,
            "item_code": item_code,
        }
        if batch_no:
            stock_filters["batch_no"] = batch_no

        stock_rows = frappe.get_all(
            "WH Cell Stock",
            filters=stock_filters,
            fields=["qty", "uom"],
            limit_page_length=0,
        )
        available_qty = sum(flt(row.qty) for row in stock_rows)
        if required_qty and available_qty + 0.0001 < required_qty:
            continue

        label = f"{cell.cell_code or cell.name} {cell.cell_label or ''}".strip()
        if search_text and search_text not in label.lower() and search_text not in (cell.name or "").lower():
            continue

        results.append(
            (
                cell.name,
                f"{cell.cell_code or cell.name} - {cell.cell_label or ''}".strip(" -"),
                f"{available_qty:g} {(stock_rows[0].uom if stock_rows else '')}".strip(),
            )
        )

    return results[start : start + page_len]


def _normalize_bridge_url(value):
    bridge_url = cstr(value).strip().rstrip("/")
    if not bridge_url:
        frappe.throw(_("WCS Bridge URL is required"))

    return bridge_url


def _bridge_request(method, url, headers=None, json_payload=None, timeout=15):
    try:
        response = requests.request(
            method,
            url,
            headers=headers,
            json=json_payload,
            timeout=timeout,
        )
        response.raise_for_status()
    except requests.HTTPError as exc:
        message = _extract_bridge_error(exc.response)
        frappe.throw(_("WCS Bridge API request failed: {0}").format(message))
    except requests.RequestException as exc:
        frappe.throw(_("Could not reach WCS Bridge API at {0}: {1}").format(url, exc))

    if not response.content:
        return {}

    try:
        return response.json()
    except ValueError:
        return {"raw": response.text}


def _extract_bridge_error(response):
    if not response:
        return _("Unknown bridge error")

    try:
        payload = response.json() or {}
    except ValueError:
        payload = {}

    return payload.get("message") or payload.get("error") or response.text or _("Unknown bridge error")


def _get_local_simulator_configuration_path():
    repo_root = Path(__file__).resolve().parents[4]
    config_path = repo_root / "services" / "wcs-bridge-api" / "config" / "plc-simulator-headless.json"
    if not config_path.exists():
        frappe.throw(_("Local simulator configuration file was not found: {0}").format(config_path))

    return str(config_path)

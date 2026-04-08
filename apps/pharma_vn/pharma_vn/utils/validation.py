import json

import frappe
from frappe import _


def get_json_payload(payload=None):
    if isinstance(payload, dict):
        return payload

    if isinstance(payload, str) and payload.strip():
        return json.loads(payload)

    request = getattr(frappe.local, "request", None)
    if request:
        return request.get_json(silent=True) or dict(frappe.form_dict)

    return {}


def require_fields(payload, fields):
    missing = [field for field in fields if not payload.get(field)]
    if missing:
        frappe.throw(_("Missing required field(s): {0}").format(", ".join(missing)))


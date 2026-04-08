import frappe
from frappe import _
from frappe.utils import cstr

from pharma_vn.ai_assistant.service import chat_with_assistant, get_assistant_bootstrap
from pharma_vn.utils.response import ok
from pharma_vn.utils.validation import get_json_payload


@frappe.whitelist()
def get_bootstrap():
    return ok(_("AI assistant status loaded"), get_assistant_bootstrap())


@frappe.whitelist()
def chat(payload=None):
    data = get_json_payload(payload)
    message = cstr(data.get("message")).strip()
    if not message:
        frappe.throw(_("message is required"))

    history = data.get("history") or []
    return ok(
        _("AI assistant response ready"),
        chat_with_assistant(message=message, history=history),
    )

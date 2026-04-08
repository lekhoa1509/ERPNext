import sys
import types
from datetime import date, datetime
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[2]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))


def install_frappe_stub():
    for module_name in list(sys.modules):
        if module_name == "frappe" or module_name.startswith("frappe."):
            sys.modules.pop(module_name, None)

    frappe = types.ModuleType("frappe")
    frappe._ = lambda value, *args, **kwargs: value
    frappe._dict = lambda value: value
    frappe.session = types.SimpleNamespace(user="tester@example.com", user_fullname="Test User")
    frappe.form_dict = {}
    frappe.local = types.SimpleNamespace(request=None)
    frappe.defaults = types.SimpleNamespace(get_user_default=lambda key: None)
    frappe.has_permission = lambda **kwargs: True
    frappe.get_all = lambda *args, **kwargs: []
    frappe.get_doc = lambda *args, **kwargs: None
    frappe.get_cached_doc = lambda *args, **kwargs: None
    frappe.get_cached_value = lambda *args, **kwargs: None
    frappe.publish_realtime = lambda *args, **kwargs: None
    frappe.db = types.SimpleNamespace(
        exists=lambda *args, **kwargs: False,
        get_value=lambda *args, **kwargs: None,
        get_default=lambda *args, **kwargs: None,
        get_single_value=lambda *args, **kwargs: None,
        has_column=lambda *args, **kwargs: False,
        set_value=lambda *args, **kwargs: None,
        table_exists=lambda *args, **kwargs: False,
        sql=lambda *args, **kwargs: [(0,)],
        commit=lambda: None,
    )

    def _throw(message):
        raise RuntimeError(message)

    frappe.throw = _throw
    frappe.whitelist = lambda *args, **kwargs: (lambda fn: fn)
    frappe.as_json = lambda value: str(value)

    utils = types.ModuleType("frappe.utils")
    utils.cint = lambda value=0: int(float(value or 0))
    utils.flt = lambda value=0: float(value or 0)
    utils.cstr = lambda value="": "" if value is None else str(value)
    utils.now_datetime = lambda: datetime(2026, 4, 8, 9, 0, 0)
    utils.nowdate = lambda: "2026-04-08"
    utils.getdate = lambda value=None: date.fromisoformat(str(value or "2026-04-08"))
    utils.date_diff = lambda end, start: (utils.getdate(end) - utils.getdate(start)).days

    sys.modules["frappe"] = frappe
    sys.modules["frappe.utils"] = utils
    return frappe

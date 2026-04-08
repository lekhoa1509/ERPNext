import frappe
from frappe import _


def get_data():
    return [
        {
            "module_name": "Pharma Operations",
            "label": _("Pharma Operations"),
            "color": "green",
            "icon": "fa fa-medkit",
            "type": "module",
        },
        {
            "module_name": "Pharma Integrations",
            "label": _("Pharma Integrations"),
            "color": "blue",
            "icon": "fa fa-plug",
            "type": "module",
        },
        {
            "module_name": "Warehouse Layout 2D",
            "label": _("Warehouse Layout 2D"),
            "color": "orange",
            "icon": "fa fa-th-large",
            "type": "module",
        },
        {
            "module_name": "Dynamic Forms",
            "label": _("Dynamic Forms"),
            "color": "teal",
            "icon": "fa fa-wpforms",
            "type": "module",
        },
    ]

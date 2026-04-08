import json
import re

import frappe
from frappe import _
from frappe.utils import cint, cstr, flt


SUPPORTED_FIELD_TYPES = {
    "Data",
    "Small Text",
    "Long Text",
    "Int",
    "Float",
    "Currency",
    "Check",
    "Date",
    "Datetime",
    "Select",
    "Link",
    "Section Break",
    "Column Break",
}
LAYOUT_FIELD_TYPES = {"Section Break", "Column Break"}


def build_schema(doc):
    fields = []
    used_fieldnames = set()

    for index, row in enumerate(doc.fields_meta or [], start=1):
        fieldtype = cstr(getattr(row, "fieldtype", "")).strip()
        label = cstr(getattr(row, "label", "")).strip()
        fieldname = cstr(getattr(row, "fieldname", "")).strip()

        if fieldtype not in SUPPORTED_FIELD_TYPES:
            frappe.throw(_("Row {0}: Unsupported field type {1}").format(index, fieldtype))

        if fieldtype not in LAYOUT_FIELD_TYPES and not label:
            frappe.throw(_("Row {0}: Label is required").format(index))

        if fieldtype not in LAYOUT_FIELD_TYPES:
            fieldname = fieldname or scrub_fieldname(label)
            if not fieldname:
                frappe.throw(_("Row {0}: Fieldname could not be generated").format(index))
            if fieldname in used_fieldnames:
                frappe.throw(_("Row {0}: Duplicate fieldname {1}").format(index, fieldname))
            used_fieldnames.add(fieldname)
            row.fieldname = fieldname
        else:
            row.fieldname = ""

        options = normalize_options(getattr(row, "options", ""))
        if fieldtype == "Select" and not options:
            frappe.throw(_("Row {0}: Select fields require options").format(index))
        if fieldtype == "Link" and not cstr(getattr(row, "link_doctype", "")).strip():
            frappe.throw(_("Row {0}: Link fields require a Link DocType").format(index))

        field_schema = {
            "idx": index,
            "label": label,
            "fieldname": row.fieldname,
            "fieldtype": fieldtype,
            "reqd": cint(getattr(row, "reqd", 0)),
            "options": options,
            "link_doctype": cstr(getattr(row, "link_doctype", "")).strip(),
            "default_value": cstr(getattr(row, "default_value", "")),
            "placeholder": cstr(getattr(row, "placeholder", "")),
            "description": cstr(getattr(row, "description", "")),
            "width": cstr(getattr(row, "width", "Full")) or "Full",
            "is_layout": fieldtype in LAYOUT_FIELD_TYPES,
        }
        fields.append(field_schema)

    return {
        "name": doc.name,
        "form_name": cstr(doc.form_name),
        "module": "Dynamic Forms",
        "published": cint(getattr(doc, "is_published", 0)),
        "allow_multiple": cint(getattr(doc, "allow_multiple_submissions", 1)),
        "introduction": cstr(getattr(doc, "introduction", "")),
        "success_message": cstr(getattr(doc, "success_message", "")),
        "fields": fields,
    }


def serialize_schema(schema):
    return json.dumps(schema, indent=2, ensure_ascii=True)


def parse_payload(payload):
    if payload is None:
        return {}
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, str):
        raw = payload.strip()
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            frappe.throw(_("Invalid JSON payload: {0}").format(exc))
        if not isinstance(parsed, dict):
            frappe.throw(_("Payload must be a JSON object"))
        return parsed
    frappe.throw(_("Unsupported payload format"))


def validate_submission(schema, payload):
    cleaned = {}
    payload = parse_payload(payload)

    for field in schema.get("fields", []):
        if field.get("is_layout"):
            continue

        fieldname = field.get("fieldname")
        value = payload.get(fieldname)
        cleaned[fieldname] = coerce_value(field, value)

        if field.get("reqd") and is_empty(cleaned[fieldname], field.get("fieldtype")):
            frappe.throw(_("{0} is required").format(field.get("label") or fieldname))

        if field.get("fieldtype") == "Select" and cleaned[fieldname] not in (None, "", *field.get("options", [])):
            frappe.throw(_("{0} has an invalid option").format(field.get("label") or fieldname))

    return cleaned


def coerce_value(field, value):
    fieldtype = field.get("fieldtype")

    if value in (None, ""):
        if fieldtype == "Check":
            return 0
        return None

    if fieldtype == "Int":
        return cint(value)
    if fieldtype in {"Float", "Currency"}:
        return flt(value)
    if fieldtype == "Check":
        return 1 if cint(value) else 0
    return cstr(value).strip() if isinstance(value, str) else value


def normalize_options(options):
    return [row.strip() for row in cstr(options).splitlines() if row.strip()]


def scrub_fieldname(value):
    slug = re.sub(r"[^a-z0-9_]+", "_", cstr(value).strip().lower().replace(" ", "_"))
    return re.sub(r"_+", "_", slug).strip("_")


def is_empty(value, fieldtype):
    if fieldtype == "Check":
        return False
    return value in (None, "")

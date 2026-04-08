import json
import re

import frappe
from frappe import _
from frappe.utils import cint, cstr


SUPPORTED_EXTENSION_FIELD_TYPES = {
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
    "Table",
    "Section Break",
    "Column Break",
}
LAYOUT_FIELD_TYPES = {"Section Break", "Column Break"}


def build_base_schema(target_doctype):
    meta = frappe.get_meta(target_doctype)
    fields = []

    for field in meta.fields:
        fields.append(
            {
                "fieldname": field.fieldname,
                "label": field.label,
                "fieldtype": field.fieldtype,
                "options": cstr(getattr(field, "options", "")),
                "reqd": cint(getattr(field, "reqd", 0)),
            }
        )

    return {
        "target_doctype": target_doctype,
        "field_count": len(fields),
        "fields": fields,
    }


def build_extension_plan(doc):
    target_doctype = cstr(doc.target_doctype).strip()
    if not target_doctype:
        frappe.throw(_("Target DocType is required"))

    meta = frappe.get_meta(target_doctype)
    existing_fieldnames = {field.fieldname for field in meta.fields if field.fieldname}
    generated_fieldnames = set()
    plan = []
    anchor_fallback = meta.fields[-1].fieldname if meta.fields else "name"

    for index, row in enumerate(doc.extension_fields or [], start=1):
        fieldtype = cstr(getattr(row, "fieldtype", "")).strip()
        label = cstr(getattr(row, "label", "")).strip()
        insert_after = cstr(getattr(row, "insert_after", "")).strip() or anchor_fallback
        requested_fieldname = cstr(getattr(row, "reference_fieldname", "")).strip()

        if fieldtype not in SUPPORTED_EXTENSION_FIELD_TYPES:
            frappe.throw(_("Row {0}: Unsupported field type {1}").format(index, fieldtype))

        if fieldtype not in LAYOUT_FIELD_TYPES and not label:
            frappe.throw(_("Row {0}: Label is required").format(index))

        if insert_after not in existing_fieldnames and insert_after not in generated_fieldnames:
            frappe.throw(_("Row {0}: Insert After field {1} does not exist on {2}").format(index, insert_after, target_doctype))

        if fieldtype == "Select" and not normalize_options(getattr(row, "options", "")):
            frappe.throw(_("Row {0}: Select fields require options").format(index))

        if fieldtype == "Link" and not cstr(getattr(row, "link_doctype", "")).strip():
            frappe.throw(_("Row {0}: Link fields require a Link DocType").format(index))

        if fieldtype == "Table" and not cstr(getattr(row, "table_doctype", "")).strip():
            frappe.throw(_("Row {0}: Table fields require a Child Table DocType").format(index))

        managed_fieldname = build_managed_fieldname(
            cstr(doc.extension_name or doc.name or "extension"),
            requested_fieldname or label or f"field_{index}",
        )

        if managed_fieldname in generated_fieldnames:
            frappe.throw(_("Row {0}: Duplicate managed fieldname {1}").format(index, managed_fieldname))

        if managed_fieldname in existing_fieldnames and not frappe.db.exists(
            "Custom Field", {"dt": target_doctype, "fieldname": managed_fieldname}
        ):
            frappe.throw(
                _("Row {0}: Fieldname {1} already exists as a standard field on {2}").format(
                    index, managed_fieldname, target_doctype
                )
            )

        generated_fieldnames.add(managed_fieldname)
        row.custom_field_name = managed_fieldname
        anchor_fallback = managed_fieldname

        plan.append(
            {
                "idx": index,
                "label": label,
                "fieldtype": fieldtype,
                "fieldname": managed_fieldname,
                "insert_after": insert_after,
                "reqd": cint(getattr(row, "reqd", 0)),
                "options": build_field_options(row, fieldtype),
                "description": cstr(getattr(row, "description", "")).strip(),
                "default": cstr(getattr(row, "default_value", "")).strip(),
                "allow_on_submit": cint(getattr(row, "allow_on_submit", 0)),
                "in_list_view": cint(getattr(row, "in_list_view", 0)),
                "hidden": cint(getattr(row, "hidden", 0)),
            }
        )

    return {
        "target_doctype": target_doctype,
        "extension_name": cstr(doc.extension_name or doc.name),
        "rows": plan,
    }


def apply_extension(doc):
    plan = build_extension_plan(doc)
    target_doctype = plan["target_doctype"]

    for row in plan["rows"]:
        custom_field = get_or_create_custom_field(target_doctype, row["fieldname"])
        custom_field.label = row["label"]
        custom_field.fieldtype = row["fieldtype"]
        custom_field.insert_after = row["insert_after"]
        custom_field.reqd = row["reqd"]
        custom_field.options = row["options"]
        custom_field.description = row["description"]
        custom_field.default = row["default"]
        custom_field.allow_on_submit = row["allow_on_submit"]
        custom_field.in_list_view = row["in_list_view"]
        custom_field.hidden = 0
        custom_field.save(ignore_permissions=True)

        write_extension_log(doc, "Apply", _("Applied field {0} on {1}").format(row["fieldname"], target_doctype), row["fieldname"])

    doc.status = "Applied"
    doc.managed_fields_json = json.dumps(plan["rows"], indent=2, ensure_ascii=True)
    doc.db_set("status", doc.status, update_modified=False)
    doc.db_set("managed_fields_json", doc.managed_fields_json, update_modified=False)
    frappe.clear_cache(doctype=target_doctype)
    announcement = announce_extension_update(doc, plan)
    plan["announcement"] = announcement
    return plan


def disable_extension(doc):
    target_doctype = cstr(doc.target_doctype).strip()
    managed_fields = load_managed_fields(doc)

    for row in managed_fields:
        custom_field = get_existing_custom_field(target_doctype, row["fieldname"])
        if not custom_field:
            continue
        custom_field.hidden = 1
        custom_field.save(ignore_permissions=True)
        write_extension_log(doc, "Disable", _("Disabled field {0} on {1}").format(row["fieldname"], target_doctype), row["fieldname"])

    doc.status = "Disabled"
    doc.db_set("status", doc.status, update_modified=False)
    frappe.clear_cache(doctype=target_doctype)
    return managed_fields


def uninstall_extension(doc):
    target_doctype = cstr(doc.target_doctype).strip()
    managed_fields = load_managed_fields(doc)

    for row in managed_fields:
        custom_field = get_existing_custom_field(target_doctype, row["fieldname"])
        if not custom_field:
            continue
        frappe.delete_doc("Custom Field", custom_field.name, ignore_permissions=True, force=True)
        write_extension_log(doc, "Uninstall", _("Removed field {0} from {1}").format(row["fieldname"], target_doctype), row["fieldname"])

    doc.status = "Uninstalled"
    doc.managed_fields_json = json.dumps([], indent=2, ensure_ascii=True)
    doc.db_set("status", doc.status, update_modified=False)
    doc.db_set("managed_fields_json", doc.managed_fields_json, update_modified=False)
    frappe.clear_cache(doctype=target_doctype)
    return managed_fields


def load_managed_fields(doc):
    raw = cstr(getattr(doc, "managed_fields_json", "")).strip()
    if not raw:
        return build_extension_plan(doc)["rows"]
    return json.loads(raw)


def refresh_reference_json(doc):
    if doc.target_doctype:
        doc.base_schema_json = json.dumps(build_base_schema(doc.target_doctype), indent=2, ensure_ascii=True)
    else:
        doc.base_schema_json = ""

    if doc.extension_fields:
        doc.extension_plan_json = json.dumps(build_extension_plan(doc), indent=2, ensure_ascii=True)
    else:
        doc.extension_plan_json = ""


def get_target_field_options(target_doctype):
    schema = build_base_schema(target_doctype)
    return [
        {
            "label": "{0} ({1})".format(field["label"] or field["fieldname"], field["fieldname"]),
            "value": field["fieldname"],
        }
        for field in schema["fields"]
        if field["fieldname"]
    ]


def build_field_options(row, fieldtype):
    if fieldtype == "Select":
        return cstr(getattr(row, "options", "")).strip()
    if fieldtype == "Link":
        return cstr(getattr(row, "link_doctype", "")).strip()
    if fieldtype == "Table":
        return cstr(getattr(row, "table_doctype", "")).strip()
    return ""


def get_or_create_custom_field(target_doctype, fieldname):
    existing = get_existing_custom_field(target_doctype, fieldname)
    if existing:
        return existing

    return frappe.get_doc(
        {
            "doctype": "Custom Field",
            "dt": target_doctype,
            "fieldname": fieldname,
        }
    )


def get_existing_custom_field(target_doctype, fieldname):
    custom_field_name = frappe.db.get_value("Custom Field", {"dt": target_doctype, "fieldname": fieldname}, "name")
    if not custom_field_name:
        return None
    return frappe.get_doc("Custom Field", custom_field_name)


def write_extension_log(doc, action, detail, custom_field_name=None):
    frappe.get_doc(
        {
            "doctype": "Form Extension Log",
            "extension_manager": doc.name,
            "target_doctype": doc.target_doctype,
            "action": action,
            "custom_field_name": custom_field_name,
            "detail": detail,
            "performed_by": frappe.session.user,
        }
    ).insert(ignore_permissions=True)


def announce_extension_update(doc, plan):
    subject = _("Form extension applied: {0}").format(doc.extension_name or doc.name)
    message = _(
        "{0} updated {1} with {2} managed field(s). Users should sign out and sign back in to load the latest Desk form layout."
    ).format(
        frappe.session.user_fullname or frappe.session.user,
        plan["target_doctype"],
        len(plan["rows"]),
    )
    users = get_system_notification_users()

    for user in users:
        frappe.get_doc(
            {
                "doctype": "Notification Log",
                "for_user": user,
                "type": "Alert",
                "subject": subject,
                "email_content": message,
                "document_type": "Form Extension Manager",
                "document_name": doc.name,
            }
        ).insert(ignore_permissions=True)

        publish_notification_realtime(user=user, subject=subject, message=message, document_name=doc.name)

    return {
        "subject": subject,
        "message": message,
        "reload_required": 1,
        "users_notified": len(users),
    }


def get_system_notification_users():
    try:
        users = frappe.get_all(
            "User",
            filters={"enabled": 1, "user_type": "System User"},
            pluck="name",
        )
    except TypeError:
        users = frappe.get_all("User", pluck="name")

    return sorted({user for user in users if user and user != "Guest"})


def publish_notification_realtime(*, user, subject, message, document_name):
    if not hasattr(frappe, "publish_realtime"):
        return

    payload = {
        "type": "Alert",
        "subject": subject,
        "message": message,
        "document_type": "Form Extension Manager",
        "document_name": document_name,
    }

    for event in ("notification", "desk_notification", "list_update"):
        try:
            frappe.publish_realtime(event, payload, user=user)
        except TypeError:
            try:
                frappe.publish_realtime(event=event, message=payload, user=user)
            except Exception:
                continue
        except Exception:
            continue


def build_managed_fieldname(extension_name, label):
    extension_slug = slugify(extension_name)[:20]
    label_slug = slugify(label)[:24]
    managed = f"ext_{extension_slug}_{label_slug}".strip("_")
    return managed[:61]


def normalize_options(options):
    return [row.strip() for row in cstr(options).splitlines() if row.strip()]


def slugify(value):
    slug = re.sub(r"[^a-z0-9_]+", "_", cstr(value).strip().lower().replace(" ", "_"))
    return re.sub(r"_+", "_", slug).strip("_")

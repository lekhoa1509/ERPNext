import json

import frappe
from frappe import _
from frappe.utils import cint, cstr


def resolve_user_access(user):
    profile_name = frappe.db.get_value("User Access Profile", {"user": user}, "name")
    if not profile_name:
        return {
            "user": user,
            "group_assignments": [],
            "overrides": [],
            "effective_permissions": [],
        }

    profile = frappe.get_doc("User Access Profile", profile_name)
    return resolve_profile_access(profile)


def resolve_profile_access(profile):
    decision_map = {}
    group_assignments = []

    sorted_groups = sorted(
        [row for row in profile.group_assignments or [] if cint(getattr(row, "is_active", 1))],
        key=lambda row: cint(getattr(row, "priority", 0)),
        reverse=True,
    )

    for row in sorted_groups:
        group_doc = frappe.get_doc("Access Group", row.access_group)
        group_assignments.append(
            {
                "access_group": row.access_group,
                "priority": cint(getattr(row, "priority", 0)),
            }
        )
        for permission in group_doc.permissions_matrix or []:
            function_code = cstr(getattr(permission, "function_access", "")).strip()
            if not function_code:
                continue

            existing = decision_map.get(function_code)
            if existing and existing["source"] == "group" and existing["priority"] > cint(row.priority):
                continue

            decision_map[function_code] = {
                "function_access": function_code,
                "label": frappe.db.get_value("Function Access", function_code, "label") or function_code,
                "access_mode": cstr(getattr(permission, "access_mode", "Allow")) or "Allow",
                "source": "group",
                "source_name": row.access_group,
                "priority": cint(getattr(row, "priority", 0)),
            }

    overrides = []
    for override in profile.user_overrides or []:
        function_code = cstr(getattr(override, "function_access", "")).strip()
        if not function_code:
            continue

        access_mode = cstr(getattr(override, "access_mode", "Allow")) or "Allow"
        decision_map[function_code] = {
            "function_access": function_code,
            "label": frappe.db.get_value("Function Access", function_code, "label") or function_code,
            "access_mode": access_mode,
            "source": "user",
            "source_name": profile.user,
            "priority": 999999,
        }
        overrides.append({"function_access": function_code, "access_mode": access_mode})

    effective_permissions = sorted(
        decision_map.values(),
        key=lambda row: (row["label"] or row["function_access"], row["function_access"]),
    )

    return {
        "user": profile.user,
        "group_assignments": group_assignments,
        "overrides": overrides,
        "effective_permissions": effective_permissions,
    }


def refresh_profile_resolution(profile):
    profile.effective_permissions_json = json.dumps(
        resolve_profile_access(profile),
        indent=2,
        ensure_ascii=True,
    )


def has_function_access(user, function_code, default=False):
    resolution = resolve_user_access(user)
    for item in resolution["effective_permissions"]:
        if item["function_access"] == function_code:
            return item["access_mode"] == "Allow"
    return default


def require_function_access(function_code, user=None):
    target_user = user or frappe.session.user
    if not has_function_access(target_user, function_code):
        frappe.throw(_("You do not have access to function {0}").format(function_code))

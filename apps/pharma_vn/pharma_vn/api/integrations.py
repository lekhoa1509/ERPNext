import frappe
from frappe import _
from frappe.utils import flt, now_datetime

from pharma_vn.services.quality import build_recall_values, build_temperature_log_values
from pharma_vn.utils.batch import update_batch_fields
from pharma_vn.utils.response import ok
from pharma_vn.utils.validation import get_json_payload, require_fields


@frappe.whitelist(allow_guest=True)
def log_temperature(payload=None):
    data = get_json_payload(payload)
    require_fields(data, ["warehouse", "sensor_id", "temperature_c"])
    # API nay cho phep guest de sau nay de dang nhan du lieu tu IoT gateway / webhook.
    temperature_plan = build_temperature_log_values(
        {
            **data,
            "temperature_c": flt(data["temperature_c"]),
            "min_temp": flt(data.get("min_temp", 0)),
            "max_temp": flt(data.get("max_temp", 25)),
        },
        recorded_at=now_datetime(),
    )

    temp_log = frappe.get_doc(
        {
            "doctype": "PH Temperature Log",
            **temperature_plan["log_values"],
        }
    )
    temp_log.insert(ignore_permissions=True)

    if temperature_plan["batch_updates"]:
        # Khi co excursion, khoa batch o muc Batch truoc khi nghiep vu kho su dung tiep.
        update_batch_fields(data["batch_no"], temperature_plan["batch_updates"])

    return ok(
        _("Temperature log recorded"),
        {
            "name": temp_log.name,
            "action_required": temperature_plan["evaluation"]["action_required"],
            "excursion_type": temperature_plan["evaluation"]["excursion"],
        },
    )


@frappe.whitelist()
def trigger_recall(payload=None):
    data = get_json_payload(payload)
    require_fields(data, ["company", "item_code", "batch_no", "reason"])

    # Dem truoc so Delivery Note bi anh huong de team QA/Regulatory uu tien xu ly.
    affected_delivery_count = frappe.db.sql(
        """
        select count(distinct dni.parent)
        from `tabDelivery Note Item` dni
        inner join `tabDelivery Note` dn on dn.name = dni.parent
        where dn.docstatus = 1
          and dni.item_code = %(item_code)s
          and dni.batch_no = %(batch_no)s
        """,
        {
            "item_code": data["item_code"],
            "batch_no": data["batch_no"],
        },
    )[0][0]

    recall_values = build_recall_values(
        data,
        initiated_by=frappe.session.user,
        initiated_on=now_datetime(),
        affected_delivery_count=affected_delivery_count,
    )
    recall_values["status"] = "Open"
    recall_doc = frappe.get_doc({"doctype": "PH Recall Case", **recall_values})
    recall_doc.insert(ignore_permissions=True)

    # Recall phai dong thoi doi trang thai batch de chan tiep tuc xuat.
    update_batch_fields(data["batch_no"], {"batch_status": "Recalled"})

    return ok(
        _("Recall case created"),
        {"name": recall_doc.name, "affected_delivery_count": affected_delivery_count},
    )

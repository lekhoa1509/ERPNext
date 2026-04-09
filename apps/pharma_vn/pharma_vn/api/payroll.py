import frappe
from frappe.utils import formatdate, get_first_day, get_last_day, getdate

from pharma_vn.hrm.payroll import (
    calculate_salary,
    generate_monthly_salary_slips,
    generate_salary,
    get_payroll_formula_settings,
    update_payroll_formula_settings,
)
from pharma_vn.hrm.service import HRM_RECORD_TABLE


@frappe.whitelist()
def preview_salary(employee, from_date, to_date):
    return calculate_salary(employee, from_date, to_date)


@frappe.whitelist()
def generate_salary_slip(employee, month=None, auto_submit=None):
    return generate_salary(employee=employee, month=month, auto_submit=auto_submit)


@frappe.whitelist()
def generate_salary_slips(month=None, company=None, auto_submit=None):
    result = generate_monthly_salary_slips(run_date=month, company=company, auto_submit=auto_submit)
    result["records_synced"] = sync_salary_slips_to_hrm_records(month=month, salary_slips=result.get("generated") or [])
    return result


@frappe.whitelist()
def get_formula_settings():
    return get_payroll_formula_settings()


@frappe.whitelist()
def save_formula_settings(formulas):
    if not frappe.has_permission("Payroll Automation Settings", "write"):
        frappe.throw("Bạn không có quyền cập nhật công thức tính lương.")
    return update_payroll_formula_settings(formulas)


@frappe.whitelist()
def sync_salary_slips_to_hrm_records(month=None, salary_slips=None):
    _require_hrm_record_table()
    salary_slips = frappe.parse_json(salary_slips) if isinstance(salary_slips, str) else (salary_slips or [])
    if salary_slips:
        slip_names = salary_slips
    else:
        target_date = getdate(month)
        slip_names = frappe.get_all(
            "Salary Slip",
            filters={
                "start_date": get_first_day(target_date),
                "end_date": get_last_day(target_date),
                "docstatus": ("!=", 2),
            },
            pluck="name",
        )

    synced = []
    for slip_name in slip_names:
        payload = _build_payroll_record_from_salary_slip(slip_name)
        if not payload:
            continue
        _upsert_hrm_payroll_record(payload)
        synced.append(payload["name"])

    frappe.db.commit()
    return synced


@frappe.whitelist()
def delete_payroll_record(record_name):
    _require_hrm_record_table()
    if not record_name:
        frappe.throw("Thiếu bảng lương cần xóa.")

    if frappe.db.exists("Salary Slip", record_name):
        salary_slip = frappe.get_doc("Salary Slip", record_name)
        if salary_slip.docstatus == 1:
            salary_slip.cancel()
            salary_slip.reload()
        if salary_slip.docstatus == 0:
            salary_slip.delete(ignore_permissions=True)

    frappe.db.sql(
        f"delete from `{HRM_RECORD_TABLE}` where page_key=%s and name=%s",
        ("hrm-payroll", record_name),
    )
    frappe.db.commit()
    return {"ok": True}


def _build_payroll_record_from_salary_slip(slip_name):
    if not frappe.db.exists("Salary Slip", slip_name):
        return None

    slip = frappe.get_doc("Salary Slip", slip_name)
    month_label = formatdate(slip.start_date, "mm/yyyy") if slip.start_date else slip.name
    return {
        "name": slip.name,
        "payroll_title": f"{slip.employee_name or slip.employee} - {month_label}",
        "employee_name": slip.employee_name or slip.employee,
        "employee_code": slip.employee,
        "status": _map_salary_slip_status(slip),
        "company": slip.company,
        "pay_period": str(slip.start_date) if slip.start_date else "",
        "posting_date": str(slip.end_date or slip.posting_date or ""),
        "base_salary": getattr(slip, "pharma_base_salary", 0) or slip.get("pharma_base_salary") or 0,
        "allowance_amount": getattr(slip, "pharma_allowance_total", 0) or slip.get("pharma_allowance_total") or 0,
        "deduction_amount": getattr(slip, "total_deduction", 0) or 0,
        "net_salary": getattr(slip, "net_pay", 0) or 0,
        "notes": f"Salary Slip: {slip.name}",
    }


def _upsert_hrm_payroll_record(payload):
    existing = frappe.db.sql(
        f"select name from `{HRM_RECORD_TABLE}` where page_key=%s and name=%s limit 1",
        ("hrm-payroll", payload["name"]),
    )
    normalized = {
        "title": payload.get("payroll_title"),
        "status": payload.get("status"),
        "subject": payload.get("notes") or payload.get("payroll_title"),
        "employee_code": payload.get("employee_code"),
        "employee_name": payload.get("employee_name"),
        "company": payload.get("company"),
        "posting_date": payload.get("posting_date"),
        "start_date": payload.get("pay_period"),
        "end_date": payload.get("posting_date"),
        "amount": payload.get("net_salary") or 0,
        "file_url": payload.get("file_url"),
        "payload_json": frappe.as_json(payload),
    }
    if existing:
        frappe.db.sql(
            f"""
            update `{HRM_RECORD_TABLE}`
               set title=%(title)s,
                   status=%(status)s,
                   subject=%(subject)s,
                   employee_code=%(employee_code)s,
                   employee_name=%(employee_name)s,
                   company=%(company)s,
                   posting_date=%(posting_date)s,
                   start_date=%(start_date)s,
                   end_date=%(end_date)s,
                   amount=%(amount)s,
                   file_url=%(file_url)s,
                   payload_json=%(payload_json)s
             where page_key='hrm-payroll' and name=%(name)s
            """,
            {**normalized, "name": payload["name"]},
        )
    else:
        frappe.db.sql(
            f"""
            insert into `{HRM_RECORD_TABLE}` (
                name, page_key, title, status, subject, employee_code, employee_name, company,
                posting_date, start_date, end_date, amount, file_url, payload_json, owner
            ) values (
                %(name)s, 'hrm-payroll', %(title)s, %(status)s, %(subject)s, %(employee_code)s,
                %(employee_name)s, %(company)s, %(posting_date)s, %(start_date)s, %(end_date)s,
                %(amount)s, %(file_url)s, %(payload_json)s, %(owner)s
            )
            """,
            {**normalized, "name": payload["name"], "owner": frappe.session.user},
        )


def _map_salary_slip_status(slip):
    if slip.docstatus == 1:
        return "Paid" if slip.status == "Paid" else "Submitted"
    if slip.docstatus == 2:
        return "Cancelled"
    return "Calculated"


def _require_hrm_record_table():
    exists = frappe.db.sql("show tables like %s", (HRM_RECORD_TABLE,))
    if not exists:
        frappe.throw("Thiếu bảng dữ liệu HRM custom. Hãy chạy lại thiết lập HRM trước khi đồng bộ bảng lương.")

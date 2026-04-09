import json
from datetime import date, timedelta

import frappe
from frappe.utils import cint, flt, getdate

from pharma_vn.hrm.payroll import ensure_salary_component, generate_salary
from pharma_vn.hrm.service import HRM_RECORD_TABLE


TARGET_COMPANY = "Viet An Pharma JSC"
TARGET_MONTH = "2026-03"
TARGET_SALARY_STRUCTURE = "Demo Monthly Payroll - VAP"
TARGET_HOLIDAY_LIST = "Demo Holiday List 2026 - VAP"
TARGET_EMPLOYEE_CODES = [f"HRM-DEMO-26030{i}" for i in range(1, 6)]


def enable_hrms_payroll_demo():
    frappe.set_user("Administrator")

    structure_name = _ensure_salary_structure()
    contract_rows, assignment_rows = _assign_salary_structure(structure_name)
    attendance_rows = _sync_standard_attendance()
    holiday_list = _ensure_holiday_list()
    generated_slips = _generate_salary_slips()

    frappe.db.commit()
    return {
        "salary_structure": structure_name,
        "holiday_list": holiday_list,
        "contracts_updated": contract_rows,
        "salary_structure_assignments": assignment_rows,
        "attendance_synced": attendance_rows,
        "salary_slips": generated_slips,
    }


def _ensure_salary_structure():
    ensure_salary_component("Base Salary", "Earning")
    ensure_salary_component("Overtime Pay", "Earning")
    ensure_salary_component("Social Insurance", "Deduction")
    ensure_salary_component("Personal Income Tax", "Deduction")

    if frappe.db.exists("Salary Structure", TARGET_SALARY_STRUCTURE):
        structure = frappe.get_doc("Salary Structure", TARGET_SALARY_STRUCTURE)
        if structure.docstatus == 1:
            return structure.name
        if structure.docstatus == 2:
            structure = frappe.new_doc("Salary Structure")
            structure.name = TARGET_SALARY_STRUCTURE
    else:
        structure = frappe.new_doc("Salary Structure")
        structure.name = TARGET_SALARY_STRUCTURE

    structure.company = TARGET_COMPANY
    structure.currency = "VND"
    structure.is_active = "Yes"
    structure.payroll_frequency = "Monthly"
    structure.salary_slip_based_on_timesheet = 0
    structure.set("earnings", [])
    structure.append(
        "earnings",
        {
            "salary_component": "Base Salary",
            "abbr": "BASE",
            "amount_based_on_formula": 0,
            "amount": 0,
        },
    )
    structure.set("deductions", [])

    if structure.is_new():
        structure.insert(ignore_permissions=True)
    else:
        structure.save(ignore_permissions=True)

    if structure.docstatus == 0:
        structure.submit()

    return structure.name


def _assign_salary_structure(structure_name):
    updated = []
    assignments = []
    contracts = frappe.get_all(
        "Employee Contract",
        filters={
            "employee": ("in", _get_demo_employees()),
            "company": TARGET_COMPANY,
            "docstatus": ("!=", 2),
        },
        fields=["name", "employee", "start_date"],
    )

    employee_meta = frappe.get_meta("Employee")
    has_default_salary_structure = employee_meta.has_field("default_salary_structure")

    for row in contracts:
        contract = frappe.get_doc("Employee Contract", row.name)
        frappe.db.set_value("Employee Contract", contract.name, "salary_structure", structure_name, update_modified=False)
        updated.append(contract.name)
        assignments.append(_ensure_salary_structure_assignment(contract, structure_name))

        if has_default_salary_structure:
            frappe.db.set_value("Employee", contract.employee, "default_salary_structure", structure_name, update_modified=False)

    return updated, assignments


def _ensure_salary_structure_assignment(contract, structure_name):
    from_date = str(getdate(contract.start_date))
    assignment_name = frappe.db.get_value(
        "Salary Structure Assignment",
        {
            "employee": contract.employee,
            "salary_structure": structure_name,
            "from_date": from_date,
        },
        "name",
    )

    assignment = (
        frappe.get_doc("Salary Structure Assignment", assignment_name)
        if assignment_name
        else frappe.new_doc("Salary Structure Assignment")
    )

    if assignment.docstatus == 1:
        return assignment.name

    assignment.employee = contract.employee
    assignment.salary_structure = structure_name
    assignment.from_date = from_date
    assignment.company = TARGET_COMPANY
    assignment.base = flt(getattr(contract, "base_salary", 0))

    if assignment.is_new():
        assignment.insert(ignore_permissions=True)
    else:
        assignment.save(ignore_permissions=True)

    if assignment.docstatus == 0:
        assignment.submit()

    return assignment.name


def _sync_standard_attendance():
    employee_map = _get_employee_code_map()
    rows = frappe.db.sql(
        f"""
        select name, employee_code, payload_json
          from `{HRM_RECORD_TABLE}`
         where page_key='hrm-attendance'
           and employee_code in %(codes)s
        """,
        {"codes": tuple(TARGET_EMPLOYEE_CODES)},
        as_dict=True,
    )

    synced = 0
    for row in rows:
        payload = frappe.parse_json(row.payload_json) or {}
        employee_name = employee_map.get(payload.get("employee_code"))
        attendance_date = payload.get("attendance_date")
        if not employee_name or not attendance_date:
            continue

        standard_status = "Present" if payload.get("status") == "Submitted" else "Absent"
        existing_name = frappe.db.get_value(
            "Attendance",
            {"employee": employee_name, "attendance_date": attendance_date, "docstatus": ("!=", 2)},
            "name",
        )
        attendance = frappe.get_doc("Attendance", existing_name) if existing_name else frappe.new_doc("Attendance")
        if attendance.docstatus == 1:
            attendance.cancel()
            attendance.reload()

        attendance.naming_series = "HR-ATT-.YYYY.-"
        attendance.employee = employee_name
        attendance.attendance_date = attendance_date
        attendance.status = standard_status
        attendance.company = TARGET_COMPANY
        attendance.working_hours = flt(payload.get("working_hours") or 0)

        if attendance.is_new():
            attendance.insert(ignore_permissions=True)
        else:
            attendance.save(ignore_permissions=True)

        if attendance.docstatus == 0:
            attendance.submit()
        synced += 1

    return synced


def _generate_salary_slips():
    slips = []
    for employee in _get_demo_employees():
        result = generate_salary(employee=employee, month=f"{TARGET_MONTH}-01", auto_submit=0)
        slips.append(result["salary_slip"])
    return slips


def _ensure_holiday_list():
    if frappe.db.exists("Holiday List", TARGET_HOLIDAY_LIST):
        holiday_list = frappe.get_doc("Holiday List", TARGET_HOLIDAY_LIST)
    else:
        holiday_list = frappe.new_doc("Holiday List")
        holiday_list.holiday_list_name = TARGET_HOLIDAY_LIST

    holiday_list.from_date = "2026-01-01"
    holiday_list.to_date = "2026-12-31"
    holiday_list.set("holidays", [])

    current = date(2026, 1, 1)
    end = date(2026, 12, 31)
    while current <= end:
        if current.weekday() >= 5:
            holiday_list.append(
                "holidays",
                {
                    "holiday_date": current.isoformat(),
                    "description": "Weekend",
                    "weekly_off": 1,
                },
            )
        current += timedelta(days=1)

    if holiday_list.is_new():
        holiday_list.insert(ignore_permissions=True)
    else:
        holiday_list.save(ignore_permissions=True)

    company_meta = frappe.get_meta("Company")
    if company_meta.has_field("default_holiday_list"):
        frappe.db.set_value("Company", TARGET_COMPANY, "default_holiday_list", holiday_list.name, update_modified=False)
    elif company_meta.has_field("holiday_list"):
        frappe.db.set_value("Company", TARGET_COMPANY, "holiday_list", holiday_list.name, update_modified=False)

    employee_meta = frappe.get_meta("Employee")
    if employee_meta.has_field("holiday_list"):
        for employee in _get_demo_employees():
            frappe.db.set_value("Employee", employee, "holiday_list", holiday_list.name, update_modified=False)

    _ensure_holiday_assignment("Company", TARGET_COMPANY, holiday_list.name)
    for employee in _get_demo_employees():
        _ensure_holiday_assignment("Employee", employee, holiday_list.name)

    return holiday_list.name


def _ensure_holiday_assignment(applicable_for, assigned_to, holiday_list_name):
    assignment_name = frappe.db.get_value(
        "Holiday List Assignment",
        {"applicable_for": applicable_for, "assigned_to": assigned_to, "from_date": "2026-01-01"},
        "name",
    )

    assignment = (
        frappe.get_doc("Holiday List Assignment", assignment_name)
        if assignment_name
        else frappe.new_doc("Holiday List Assignment")
    )

    if assignment.docstatus == 1 and assignment.holiday_list == holiday_list_name:
        return assignment.name

    if assignment.docstatus == 1:
        assignment.cancel()
        assignment.reload()

    assignment.naming_series = "HR-HLA-.YYYY.-"
    assignment.applicable_for = applicable_for
    assignment.assigned_to = assigned_to
    assignment.holiday_list = holiday_list_name
    assignment.from_date = "2026-01-01"

    if assignment.is_new():
        assignment.insert(ignore_permissions=True)
    else:
        assignment.save(ignore_permissions=True)

    if assignment.docstatus == 0:
        assignment.submit()

    return assignment.name


def _get_demo_employees():
    return frappe.get_all(
        "Employee",
        filters={"employee_name": ("in", _get_demo_employee_names())},
        pluck="name",
    )


def _get_demo_employee_names():
    return [
        "Nguyen Minh Chau",
        "Tran Quoc Bao",
        "Le Thanh Ngan",
        "Pham Duc Anh",
        "Vo Gia Han",
    ]


def _get_employee_code_map():
    rows = frappe.db.sql(
        f"""
        select employee_code, payload_json
          from `{HRM_RECORD_TABLE}`
         where page_key='hrm-employee-profile'
           and employee_code in %(codes)s
        """,
        {"codes": tuple(TARGET_EMPLOYEE_CODES)},
        as_dict=True,
    )
    employee_names = _get_demo_employee_names()
    employee_docs = frappe.get_all(
        "Employee",
        filters={"employee_name": ("in", employee_names)},
        fields=["name", "employee_name"],
    )
    by_name = {row.employee_name: row.name for row in employee_docs}

    output = {}
    for row in rows:
        payload = frappe.parse_json(row.payload_json) or {}
        employee_name = payload.get("full_name") or payload.get("employee_name")
        if employee_name and employee_name in by_name:
            output[row.employee_code] = by_name[employee_name]
    return output

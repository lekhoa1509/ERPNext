import calendar
from dataclasses import dataclass

import frappe
from frappe.utils import cint, flt, getdate

from pharma_vn.hrm.service import HRM_RECORD_TABLE, ensure_hrm_schema, normalize_payload


TARGET_COMPANY = "Viet An Pharma JSC"
TARGET_MONTH = "2026-03"


@dataclass(frozen=True)
class DemoEmployee:
    employee_code: str
    first_name: str
    last_name: str
    gender: str
    department: str
    designation: str
    monthly_salary: int

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def email(self):
        slug = self.employee_code.lower()
        return f"{slug}@vietanpharma.local"


DEMO_EMPLOYEES = [
    DemoEmployee("HRM-DEMO-260301", "Nguyen", "Minh Chau", "Female", "Human Resources - VAP", "HR Manager", 15000000),
    DemoEmployee("HRM-DEMO-260302", "Tran", "Quoc Bao", "Male", "Operations - VAP", "Manager", 16250000),
    DemoEmployee("HRM-DEMO-260303", "Le", "Thanh Ngan", "Female", "Quality Management - VAP", "Analyst", 17500000),
    DemoEmployee("HRM-DEMO-260304", "Pham", "Duc Anh", "Male", "Sales - VAP", "Business Analyst", 18800000),
    DemoEmployee("HRM-DEMO-260305", "Vo", "Gia Han", "Female", "Marketing - VAP", "Administrative Officer", 19950000),
]


def seed_demo_hrm_march_2026():
    frappe.set_user("Administrator")
    ensure_hrm_schema()

    if not frappe.db.exists("Company", TARGET_COMPANY):
        frappe.throw(f"Company {TARGET_COMPANY} khong ton tai trong site.")

    summary = {
        "company": TARGET_COMPANY,
        "month": TARGET_MONTH,
        "employees": [],
        "contracts": [],
        "attendance_records": 0,
        "payroll_records": [],
    }

    working_days = _get_month_working_days(2026, 3)
    for index, demo in enumerate(DEMO_EMPLOYEES, start=1):
        employee_name = _upsert_employee(demo, index)
        contract_name = _upsert_employee_contract(employee_name, demo)
        attendance_count, present_days, absent_days = _upsert_hrm_attendance(employee_name, demo, working_days)
        payroll_name = _upsert_hrm_payroll(employee_name, demo, working_days, present_days)
        _upsert_hrm_employee_profile(demo)
        _upsert_hrm_contract_card(demo)

        summary["employees"].append(employee_name)
        summary["contracts"].append(contract_name)
        summary["attendance_records"] += attendance_count
        summary["payroll_records"].append(
            {
                "employee": employee_name,
                "employee_code": demo.employee_code,
                "payroll_record": payroll_name,
                "present_days": present_days,
                "absent_days": absent_days,
                "salary": demo.monthly_salary,
            }
        )

    frappe.db.commit()
    return summary


def _upsert_employee(demo, index):
    employee_name = None
    employee_meta = frappe.get_meta("Employee")
    if employee_meta.has_field("custom_employee_code"):
        employee_name = frappe.db.get_value("Employee", {"custom_employee_code": demo.employee_code}, "name")
    if not employee_name:
        employee_name = frappe.db.get_value("Employee", {"employee_name": demo.full_name, "company": TARGET_COMPANY}, "name")

    if employee_name:
        employee = frappe.get_doc("Employee", employee_name)
    else:
        employee = frappe.new_doc("Employee")
        employee.naming_series = "HR-EMP-"

    employee.first_name = demo.first_name
    employee.last_name = demo.last_name
    employee.employee_name = demo.full_name
    employee.company = TARGET_COMPANY
    employee.status = "Active"
    employee.date_of_joining = "2026-01-06"
    employee.department = demo.department
    employee.designation = demo.designation
    employee.personal_email = demo.email
    employee.cell_number = f"090{index}26030{index}"

    if employee_meta.has_field("custom_employee_code"):
        employee.custom_employee_code = demo.employee_code

    if employee.is_new():
        employee.insert(ignore_permissions=True, ignore_mandatory=True)
    else:
        employee.save(ignore_permissions=True)

    return employee.name


def _upsert_employee_contract(employee_name, demo):
    contract_name = frappe.db.get_value(
        "Employee Contract",
        {"employee": employee_name, "start_date": "2026-03-01", "company": TARGET_COMPANY},
        "name",
    )

    if contract_name:
        contract = frappe.get_doc("Employee Contract", contract_name)
        if contract.docstatus == 1:
            contract.cancel()
            contract.reload()
    else:
        contract = frappe.new_doc("Employee Contract")

    contract.employee = employee_name
    contract.company = TARGET_COMPANY
    contract.status = "Active"
    contract.salary_type = "Fixed"
    contract.base_salary = demo.monthly_salary
    contract.start_date = "2026-03-01"
    contract.end_date = "2026-12-31"
    contract.standard_working_hours = 208
    if hasattr(contract, "standard_working_hours_per_day"):
        contract.standard_working_hours_per_day = 8
    contract.notes = f"Demo contract seeded for payroll testing in {TARGET_MONTH}."

    if contract.is_new():
        contract.insert(ignore_permissions=True)
    else:
        contract.save(ignore_permissions=True)

    if contract.docstatus == 0:
        contract.submit()

    return contract.name


def _upsert_hrm_employee_profile(demo):
    payload = {
        "full_name": demo.full_name,
        "employee_code": demo.employee_code,
        "status": "Active",
        "company": TARGET_COMPANY,
        "department": demo.department,
        "designation": demo.designation,
        "join_date": "2026-01-06",
        "gender": "Nữ" if demo.gender == "Female" else "Nam",
        "phone": "",
        "email": demo.email,
        "notes": f"Demo employee for payroll testing in {TARGET_MONTH}.",
    }
    _upsert_hrm_record("hrm-employee-profile", demo.employee_code, payload)


def _upsert_hrm_contract_card(demo):
    payload = {
        "contract_title": f"HDLD {demo.full_name}",
        "employee_name": demo.full_name,
        "employee_code": demo.employee_code,
        "status": "Active",
        "company": TARGET_COMPANY,
        "contract_type": "Hợp đồng lao động",
        "contract_number": f"HD-{demo.employee_code[-4:]}",
        "contract_start": "2026-03-01",
        "contract_end": "2026-12-31",
        "salary_amount": demo.monthly_salary,
        "notes": "Seed demo for payroll testing.",
    }
    _upsert_hrm_record("hrm-contracts", demo.employee_code, payload)


def _upsert_hrm_attendance(employee_name, demo, working_days):
    present_days = 0
    absent_days = 0
    record_count = 0

    for date_value in working_days:
        status = "Submitted"
        working_hours = 8
        overtime_hours = 0
        notes = "Ca hanh chinh."

        if _is_demo_absent_day(demo.employee_code, date_value):
            status = "Draft"
            working_hours = 0
            notes = "Vang mat demo."
            absent_days += 1
        else:
            present_days += 1
            if date_value.day in {7, 14, 21, 28}:
                overtime_hours = 1.5
                working_hours = 9.5
                notes = "Co tang ca demo."

        payload = {
            "attendance_title": f"{demo.full_name} - {date_value}",
            "employee_name": demo.full_name,
            "employee_code": demo.employee_code,
            "status": status,
            "company": TARGET_COMPANY,
            "attendance_date": str(date_value),
            "shift_name": "Ca hanh chinh",
            "check_in": "08:00",
            "check_out": "17:00" if working_hours <= 8 else "18:30",
            "working_hours": working_hours,
            "overtime_hours": overtime_hours,
            "source": "Seed Demo",
            "notes": notes,
        }
        _upsert_hrm_record("hrm-attendance", f"{demo.employee_code}-{date_value}", payload)
        record_count += 1

    return record_count, present_days, absent_days


def _upsert_hrm_payroll(employee_name, demo, working_days, present_days):
    working_day_count = len(working_days)
    base_salary = flt(demo.monthly_salary)
    net_salary = round(base_salary * (present_days / working_day_count), 2) if working_day_count else base_salary
    deduction_amount = round(base_salary - net_salary, 2)

    payload = {
        "payroll_title": f"{demo.full_name} - {TARGET_MONTH}",
        "employee_name": demo.full_name,
        "employee_code": demo.employee_code,
        "status": "Calculated",
        "company": TARGET_COMPANY,
        "pay_period": TARGET_MONTH,
        "posting_date": "2026-03-31",
        "base_salary": base_salary,
        "allowance_amount": 0,
        "deduction_amount": deduction_amount,
        "net_salary": net_salary,
        "payment_method": "Bank Transfer",
        "notes": f"Demo payroll seeded from custom HRM attendance. ERPNext Salary Slip is not installed on this site.",
    }
    return _upsert_hrm_record("hrm-payroll", demo.employee_code, payload)


def _upsert_hrm_record(page_key, unique_key, payload):
    name = f"SEED-{page_key.upper()}-{frappe.scrub(unique_key).upper()}"[:140]
    normalized = normalize_payload(page_key, payload)
    exists = frappe.db.sql(
        f"select name from `{HRM_RECORD_TABLE}` where name=%s and page_key=%s limit 1",
        (name, page_key),
    )

    if exists:
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
                   payload_json=%(payload_json)s,
                   owner=%(owner)s
             where name=%(name)s and page_key=%(page_key)s
            """,
            {**normalized, "name": name, "page_key": page_key, "owner": "Administrator"},
        )
        return name

    frappe.db.sql(
        f"""
        insert into `{HRM_RECORD_TABLE}` (
            name, page_key, title, status, subject, employee_code, employee_name, company,
            posting_date, start_date, end_date, amount, file_url, payload_json, owner
        ) values (
            %(name)s, %(page_key)s, %(title)s, %(status)s, %(subject)s, %(employee_code)s,
            %(employee_name)s, %(company)s, %(posting_date)s, %(start_date)s, %(end_date)s,
            %(amount)s, %(file_url)s, %(payload_json)s, %(owner)s
        )
        """,
        {**normalized, "name": name, "page_key": page_key, "owner": "Administrator"},
    )
    return name


def _get_month_working_days(year, month):
    _, last_day = calendar.monthrange(year, month)
    dates = []
    for day in range(1, last_day + 1):
        value = getdate(f"{year}-{month:02d}-{day:02d}")
        if value.weekday() < 5:
            dates.append(value)
    return dates


def _is_demo_absent_day(employee_code, date_value):
    checksum = sum(ord(char) for char in f"{employee_code}-{date_value}")
    return cint(checksum % 11 == 0)

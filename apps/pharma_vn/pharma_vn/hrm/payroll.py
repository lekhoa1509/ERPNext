import json
import ast
from datetime import timedelta

import frappe
from frappe.utils import add_days, cint, flt, get_first_day, get_last_day, getdate, today


DEFAULT_SETTINGS = {
    "enable_payroll_automation": 1,
    "auto_generate_salary_slip": 0,
    "auto_submit_salary_slip": 0,
    "salary_slip_series": "Sal Slip/.YYYY./.#####",
    "social_insurance_rate": 8,
    "overtime_multiplier": 1.5,
    "personal_tax_exemption": 0,
    "standard_working_hours_per_day": 8,
    "tax_slabs": [],
    "base_salary_formula": "contract_base_salary / max(standard_working_days, 1) * payable_working_days",
    "overtime_formula": "overtime_hours * hourly_rate * overtime_multiplier",
    "social_insurance_formula": "base_salary * social_insurance_rate / 100",
    "taxable_income_formula": "max(gross_salary - social_insurance - taxable_income_reduction - personal_tax_exemption, 0)",
    "net_salary_formula": "gross_salary - total_deduction",
}

FORMULA_FIELDS = (
    "base_salary_formula",
    "overtime_formula",
    "social_insurance_formula",
    "taxable_income_formula",
    "net_salary_formula",
)
VARIABLE_DEFINITIONS = {
    "contract_base_salary": {"label": "Lương hợp đồng", "group": "Hợp đồng"},
    "payable_working_days": {"label": "Công thực tế", "group": "Chấm công"},
    "standard_working_days": {"label": "Công chuẩn tháng", "group": "Chấm công"},
    "total_working_hours": {"label": "Tổng giờ công", "group": "Chấm công"},
    "overtime_hours": {"label": "Giờ tăng ca", "group": "Chấm công"},
    "hourly_rate": {"label": "Lương giờ", "group": "Hợp đồng"},
    "overtime_multiplier": {"label": "Hệ số tăng ca", "group": "Thiết lập"},
    "base_salary": {"label": "Lương cơ bản", "group": "Hợp đồng"},
    "social_insurance_rate": {"label": "Tỷ lệ BHXH", "group": "Thiết lập"},
    "gross_salary": {"label": "Tổng thu nhập", "group": "Tính lương"},
    "social_insurance": {"label": "Tiền BHXH", "group": "Tính lương"},
    "taxable_income_reduction": {"label": "Giảm trừ chịu thuế", "group": "Khấu trừ"},
    "personal_tax_exemption": {"label": "Miễn trừ thuế TNCN", "group": "Thiết lập"},
    "total_deduction": {"label": "Tổng khấu trừ", "group": "Tính lương"},
    "kpi_score": {"label": "Điểm KPI trung bình", "group": "KPI"},
    "kpi_achievement_rate": {"label": "Tỷ lệ hoàn thành KPI", "group": "KPI"},
}
FORMULA_VARIABLES = {
    "base_salary_formula": [
        "contract_base_salary",
        "payable_working_days",
        "standard_working_days",
        "total_working_hours",
        "hourly_rate",
        "kpi_score",
        "kpi_achievement_rate",
    ],
    "overtime_formula": [
        "overtime_hours",
        "hourly_rate",
        "overtime_multiplier",
        "kpi_score",
        "kpi_achievement_rate",
    ],
    "social_insurance_formula": [
        "base_salary",
        "social_insurance_rate",
        "kpi_score",
        "kpi_achievement_rate",
    ],
    "taxable_income_formula": [
        "gross_salary",
        "social_insurance",
        "taxable_income_reduction",
        "personal_tax_exemption",
        "kpi_score",
        "kpi_achievement_rate",
    ],
    "net_salary_formula": [
        "gross_salary",
        "total_deduction",
        "base_salary",
        "kpi_score",
        "kpi_achievement_rate",
    ],
}
FORMULA_LABELS = {
    "base_salary_formula": "Công thức lương cơ bản",
    "overtime_formula": "Công thức tăng ca",
    "social_insurance_formula": "Công thức BHXH",
    "taxable_income_formula": "Công thức thu nhập tính thuế",
    "net_salary_formula": "Công thức thực lĩnh",
}
ALLOWED_FORMULA_FUNCTIONS = {
    "min": min,
    "max": max,
    "abs": abs,
    "round": round,
}


@frappe.whitelist()
def generate_salary(employee, month=None, auto_submit=None):
    ensure_payroll_dependencies()
    target_date = getdate(month or today())
    return upsert_salary_slip_for_employee(
        employee=employee,
        from_date=get_first_day(target_date),
        to_date=get_last_day(target_date),
        auto_submit=auto_submit,
    )


def before_save_salary_slip(doc, method=None):
    if not getattr(doc, "employee", None):
        return

    settings = get_payroll_settings()
    if not cint(settings.enable_payroll_automation):
        return

    from_date = getattr(doc, "start_date", None) or getattr(doc, "from_date", None)
    to_date = getattr(doc, "end_date", None) or getattr(doc, "to_date", None)
    if not from_date or not to_date:
        return

    breakdown = calculate_salary(doc.employee, from_date, to_date)
    apply_breakdown_to_salary_slip(doc, breakdown)


def calculate_salary(employee, from_date, to_date):
    ensure_payroll_dependencies(require_salary_slip=False)
    employee_doc = frappe.get_doc("Employee", employee)
    contract = get_employee_contract(employee, to_date)
    if not contract:
        frappe.throw(f"Không tìm thấy Employee Contract hiệu lực cho nhân sự {employee}.")

    attendance_rows = get_attendance_rows(employee, from_date, to_date)
    settings = get_payroll_settings()
    kpi_metrics = get_kpi_metrics(employee, from_date, to_date)

    payable_working_days = sum(1 for row in attendance_rows if row.status == "Present")
    total_working_hours = sum(flt(row.working_hours) for row in attendance_rows if row.status == "Present")
    standard_working_days = get_standard_working_days(employee, from_date, to_date)

    hourly_rate = get_hourly_rate(contract)
    contract_base_salary = flt(contract.base_salary)
    base_salary = contract_base_salary
    if contract.salary_type == "Hourly":
        base_salary = total_working_hours * hourly_rate
    else:
        base_salary = evaluate_payroll_formula(
            settings.base_salary_formula,
            {
                "contract_base_salary": contract_base_salary,
                "payable_working_days": payable_working_days,
                "standard_working_days": standard_working_days,
                "total_working_hours": total_working_hours,
                "hourly_rate": hourly_rate,
                "kpi_score": kpi_metrics["kpi_score"],
                "kpi_achievement_rate": kpi_metrics["kpi_achievement_rate"],
            },
            fieldname="base_salary_formula",
        )

    standard_hours_per_day = get_standard_hours_per_day(contract, settings)
    overtime_hours = sum(
        max(flt(row.working_hours) - standard_hours_per_day, 0)
        for row in attendance_rows
        if row.status == "Present"
    )
    overtime_salary = evaluate_payroll_formula(
        settings.overtime_formula,
        {
            "overtime_hours": overtime_hours,
            "hourly_rate": hourly_rate,
            "overtime_multiplier": flt(settings.overtime_multiplier),
            "kpi_score": kpi_metrics["kpi_score"],
            "kpi_achievement_rate": kpi_metrics["kpi_achievement_rate"],
        },
        fieldname="overtime_formula",
    )

    earnings = [{"salary_component": "Base Salary", "amount": base_salary}]
    if overtime_salary:
        earnings.append({"salary_component": "Overtime Pay", "amount": overtime_salary})

    allowance_total = 0
    for row in contract.allowances or []:
        amount = resolve_component_amount(row, base_salary)
        if not amount:
            continue
        earnings.append({"salary_component": row.component_name, "amount": amount})
        allowance_total += amount

    deductions = []
    manual_deduction_total = 0
    taxable_income_reduction = 0
    for row in contract.deductions or []:
        amount = resolve_component_amount(row, base_salary)
        if not amount:
            continue
        deductions.append({"salary_component": row.component_name, "amount": amount})
        manual_deduction_total += amount
        if cint(getattr(row, "reduce_taxable_income", 0)):
            taxable_income_reduction += amount

    gross_salary = base_salary + overtime_salary + allowance_total
    social_insurance = evaluate_payroll_formula(
        settings.social_insurance_formula,
        {
            "base_salary": base_salary,
            "social_insurance_rate": flt(settings.social_insurance_rate),
            "kpi_score": kpi_metrics["kpi_score"],
            "kpi_achievement_rate": kpi_metrics["kpi_achievement_rate"],
        },
        fieldname="social_insurance_formula",
    )
    if social_insurance:
        deductions.append({"salary_component": "Social Insurance", "amount": social_insurance})

    taxable_income = evaluate_payroll_formula(
        settings.taxable_income_formula,
        {
            "gross_salary": gross_salary,
            "social_insurance": social_insurance,
            "taxable_income_reduction": taxable_income_reduction,
            "personal_tax_exemption": flt(settings.personal_tax_exemption),
            "kpi_score": kpi_metrics["kpi_score"],
            "kpi_achievement_rate": kpi_metrics["kpi_achievement_rate"],
        },
        fieldname="taxable_income_formula",
    )
    personal_income_tax = calculate_tax(taxable_income, settings.tax_slabs or [])
    if personal_income_tax:
        deductions.append({"salary_component": "Personal Income Tax", "amount": personal_income_tax})

    total_deduction = manual_deduction_total + social_insurance + personal_income_tax
    net_salary = evaluate_payroll_formula(
        settings.net_salary_formula,
        {
            "gross_salary": gross_salary,
            "total_deduction": total_deduction,
            "base_salary": base_salary,
            "kpi_score": kpi_metrics["kpi_score"],
            "kpi_achievement_rate": kpi_metrics["kpi_achievement_rate"],
        },
        fieldname="net_salary_formula",
    )
    salary_structure = contract.salary_structure or get_employee_default_salary_structure(employee_doc)

    return {
        "employee": employee,
        "employee_name": employee_doc.employee_name,
        "company": employee_doc.company,
        "salary_structure": salary_structure,
        "employee_contract": contract.name,
        "from_date": str(getdate(from_date)),
        "to_date": str(getdate(to_date)),
        "total_working_days": payable_working_days,
        "payable_working_days": payable_working_days,
        "standard_working_days": standard_working_days,
        "total_working_hours": total_working_hours,
        "contract_base_salary": contract_base_salary,
        "overtime_hours": overtime_hours,
        "base_salary": base_salary,
        "hourly_rate": hourly_rate,
        "overtime_salary": overtime_salary,
        "allowance_total": allowance_total,
        "manual_deduction_total": manual_deduction_total,
        "social_insurance": social_insurance,
        "personal_income_tax": personal_income_tax,
        "taxable_income": taxable_income,
        "gross_salary": gross_salary,
        "total_deduction": total_deduction,
        "net_salary": net_salary,
        "kpi_score": kpi_metrics["kpi_score"],
        "kpi_achievement_rate": kpi_metrics["kpi_achievement_rate"],
        "earnings": earnings,
        "deductions": deductions,
        "attendance_details": [
            {
                "attendance_date": str(row.attendance_date),
                "working_hours": flt(row.working_hours),
                "status": row.status,
            }
            for row in attendance_rows
        ],
    }


def upsert_salary_slip_for_employee(employee, from_date, to_date, auto_submit=None):
    ensure_payroll_dependencies()
    breakdown = calculate_salary(employee, from_date, to_date)
    existing = frappe.db.get_value(
        "Salary Slip",
        {
            "employee": employee,
            "start_date": getdate(from_date),
            "end_date": getdate(to_date),
            "docstatus": ("!=", 2),
        },
        "name",
    )

    doc = frappe.get_doc("Salary Slip", existing) if existing else frappe.new_doc("Salary Slip")
    doc.employee = employee
    if hasattr(doc, "company"):
        doc.company = breakdown["company"]
    if hasattr(doc, "posting_date"):
        doc.posting_date = breakdown["to_date"]
    if hasattr(doc, "start_date"):
        doc.start_date = breakdown["from_date"]
    if hasattr(doc, "end_date"):
        doc.end_date = breakdown["to_date"]
    if hasattr(doc, "salary_structure") and breakdown["salary_structure"]:
        doc.salary_structure = breakdown["salary_structure"]
    if hasattr(doc, "naming_series"):
        doc.naming_series = get_payroll_settings().salary_slip_series

    apply_breakdown_to_salary_slip(doc, breakdown)

    if existing:
        doc.save(ignore_permissions=True)
    else:
        doc.insert(ignore_permissions=True)

    should_submit = auto_submit
    if should_submit is None:
        should_submit = cint(get_payroll_settings().auto_submit_salary_slip)
    if cint(should_submit) and doc.docstatus == 0:
        doc.submit()

    return {
        "salary_slip": doc.name,
        "docstatus": doc.docstatus,
        "breakdown": breakdown,
    }


def generate_monthly_salary_slips(run_date=None, company=None, auto_submit=None):
    ensure_payroll_dependencies()
    settings = get_payroll_settings()
    if not cint(settings.enable_payroll_automation):
        return {"generated": [], "skipped": []}

    target_date = getdate(run_date or today())
    from_date = get_first_day(target_date)
    to_date = get_last_day(target_date)
    contract_filters = {
        "status": "Active",
        "docstatus": 1,
        "start_date": ("<=", to_date),
    }
    if company:
        contract_filters["company"] = company

    contracts = frappe.get_all(
        "Employee Contract",
        filters=contract_filters,
        fields=["employee", "end_date"],
        order_by="employee asc",
    )

    generated = []
    skipped = []
    for contract in contracts:
        if contract.end_date and getdate(contract.end_date) < getdate(from_date):
            skipped.append({"employee": contract.employee, "reason": "contract_expired"})
            continue
        try:
            result = upsert_salary_slip_for_employee(
                employee=contract.employee,
                from_date=from_date,
                to_date=to_date,
                auto_submit=auto_submit,
            )
            generated.append(result["salary_slip"])
        except Exception:
            frappe.log_error(message=frappe.get_traceback(), title="Payroll Automation Failed")
            skipped.append({"employee": contract.employee, "reason": "error"})

    return {"generated": generated, "skipped": skipped}


def run_monthly_payroll_scheduler():
    settings = get_payroll_settings()
    if cint(settings.auto_generate_salary_slip):
        target_date = add_days(get_first_day(today()), -1)
        generate_monthly_salary_slips(
            run_date=target_date,
            auto_submit=settings.auto_submit_salary_slip,
        )


def apply_breakdown_to_salary_slip(doc, breakdown):
    if hasattr(doc, "salary_structure") and breakdown.get("salary_structure"):
        doc.salary_structure = breakdown["salary_structure"]
    _set_if_present(doc, "employee_contract", breakdown["employee_contract"])
    _set_if_present(doc, "pharma_total_working_days", breakdown["total_working_days"])
    _set_if_present(doc, "pharma_total_working_hours", breakdown["total_working_hours"])
    _set_if_present(doc, "pharma_overtime_hours", breakdown["overtime_hours"])
    _set_if_present(doc, "pharma_base_salary", breakdown["base_salary"])
    _set_if_present(doc, "pharma_overtime_salary", breakdown["overtime_salary"])
    _set_if_present(doc, "pharma_allowance_total", breakdown["allowance_total"])
    _set_if_present(doc, "pharma_deduction_total", breakdown["total_deduction"])
    _set_if_present(doc, "pharma_taxable_income", breakdown["taxable_income"])
    _set_if_present(doc, "pharma_payroll_breakdown_json", json.dumps(breakdown, ensure_ascii=True))

    doc.set("earnings", [])
    for row in breakdown["earnings"]:
        ensure_salary_component(row["salary_component"], "Earning")
        doc.append("earnings", {"salary_component": row["salary_component"], "amount": row["amount"]})

    doc.set("deductions", [])
    for row in breakdown["deductions"]:
        ensure_salary_component(row["salary_component"], "Deduction")
        doc.append("deductions", {"salary_component": row["salary_component"], "amount": row["amount"]})

    _set_if_present(doc, "gross_pay", breakdown["gross_salary"])
    _set_if_present(doc, "total_deduction", breakdown["total_deduction"])
    _set_if_present(doc, "net_pay", breakdown["net_salary"])
    _set_if_present(doc, "rounded_total", breakdown["net_salary"])


def get_attendance_rows(employee, from_date, to_date):
    filters = {
        "employee": employee,
        "attendance_date": ("between", [getdate(from_date), getdate(to_date)]),
        "status": ("in", ["Present", "Absent"]),
    }
    attendance_meta = frappe.get_meta("Attendance")
    if getattr(attendance_meta, "is_submittable", 0):
        filters["docstatus"] = 1

    return frappe.get_all(
        "Attendance",
        filters=filters,
        fields=["name", "attendance_date", "working_hours", "status"],
        order_by="attendance_date asc",
    )


def get_standard_working_days(employee, from_date, to_date):
    start_date = getdate(from_date)
    end_date = getdate(to_date)
    holiday_dates = set()

    try:
        from hrms.utils.holiday_list import get_holiday_dates_between_range

        holiday_dates = {
            getdate(day)
            for day in (
                get_holiday_dates_between_range(
                    assigned_to=employee,
                    start_date=start_date,
                    end_date=end_date,
                    raise_exception_for_holiday_list=False,
                )
                or []
            )
        }
    except Exception:
        holiday_dates = set()

    working_days = 0
    current = start_date
    while current <= end_date:
        if current.weekday() < 5 and current not in holiday_dates:
            working_days += 1
        current += timedelta(days=1)

    return working_days


def get_employee_contract(employee, on_date=None):
    filters = {"employee": employee, "status": "Active", "docstatus": 1}
    if on_date:
        filters["start_date"] = ("<=", getdate(on_date))

    contracts = frappe.get_all(
        "Employee Contract",
        filters=filters,
        fields=["name", "start_date", "end_date"],
        order_by="start_date desc",
    )
    target_date = getdate(on_date) if on_date else None
    for row in contracts:
        if not target_date or not row.end_date or getdate(row.end_date) >= target_date:
            return frappe.get_doc("Employee Contract", row.name)
    return None


def get_payroll_settings():
    if not frappe.db.exists("DocType", "Payroll Automation Settings"):
        return frappe._dict(DEFAULT_SETTINGS)

    try:
        doc = frappe.get_single("Payroll Automation Settings")
    except Exception:
        return frappe._dict(DEFAULT_SETTINGS)

    values = frappe._dict(DEFAULT_SETTINGS.copy())
    for key in DEFAULT_SETTINGS:
        current_value = getattr(doc, key, values[key])
        if key in FORMULA_FIELDS and not current_value:
            current_value = DEFAULT_SETTINGS[key]
        values[key] = current_value
    values.tax_slabs = sorted(doc.tax_slabs or [], key=lambda row: row.from_amount or 0)
    return values


def get_payroll_formula_settings():
    settings = get_payroll_settings()
    formulas = []
    for fieldname in FORMULA_FIELDS:
        variables = [_get_variable_meta(key) for key in FORMULA_VARIABLES[fieldname]]
        formulas.append(
            {
                "fieldname": fieldname,
                "label": FORMULA_LABELS[fieldname],
                "formula": convert_formula_to_display(settings.get(fieldname) or DEFAULT_SETTINGS[fieldname], fieldname),
                "formula_raw": settings.get(fieldname) or DEFAULT_SETTINGS[fieldname],
                "variables": variables,
                "variable_groups": _group_variables_for_dialog(variables),
            }
        )
    return {
        "formulas": formulas,
        "allowed_functions": [
            {"name": name, "label": _function_label(name), "token": f"{name}()"}
            for name in sorted(ALLOWED_FORMULA_FUNCTIONS)
        ],
    }


def update_payroll_formula_settings(formulas):
    if isinstance(formulas, str):
        formulas = json.loads(formulas)

    formula_map = {row.get("fieldname"): (row.get("formula") or "").strip() for row in formulas or []}
    payload = {}
    for fieldname in FORMULA_FIELDS:
        formula = normalize_formula_tokens(formula_map.get(fieldname) or DEFAULT_SETTINGS[fieldname], fieldname)
        validate_payroll_formula(fieldname, formula)
        payload[fieldname] = formula

    doc = frappe.get_single("Payroll Automation Settings")
    for fieldname, value in payload.items():
        setattr(doc, fieldname, value)
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return get_payroll_formula_settings()


def calculate_tax(taxable_income, tax_slabs):
    taxable_income = flt(taxable_income)
    if taxable_income <= 0 or not tax_slabs:
        return 0

    sorted_slabs = sorted(tax_slabs, key=lambda row: flt(row.from_amount))
    for row in sorted_slabs:
        upper_bound = flt(row.to_amount) if row.to_amount else None
        if taxable_income < flt(row.from_amount):
            continue
        if flt(row.deduction_amount) and (upper_bound is None or taxable_income <= upper_bound):
            return max((taxable_income * flt(row.percent) / 100) - flt(row.deduction_amount), 0)

    tax_amount = 0
    for row in sorted_slabs:
        lower = flt(row.from_amount)
        upper = flt(row.to_amount) if row.to_amount else taxable_income
        if taxable_income <= lower:
            continue
        taxable_band = min(taxable_income, upper) - lower
        if taxable_band > 0:
            tax_amount += taxable_band * flt(row.percent) / 100
        if not row.to_amount or taxable_income <= upper:
            break
    return max(tax_amount, 0)


def evaluate_payroll_formula(formula, variables, fieldname):
    normalized_formula = normalize_formula_tokens(formula, fieldname)
    validate_payroll_formula(fieldname, normalized_formula)
    compiled = ast.parse(normalized_formula, mode="eval")
    value = _safe_eval_formula(compiled.body, variables)
    return flt(value)


def validate_payroll_formula(fieldname, formula):
    formula = normalize_formula_tokens(formula, fieldname)
    if not formula or not str(formula).strip():
        frappe.throw(f"{FORMULA_LABELS.get(fieldname, fieldname)} không được để trống.")

    try:
        compiled = ast.parse(str(formula), mode="eval")
    except SyntaxError as exc:
        frappe.throw(f"{FORMULA_LABELS.get(fieldname, fieldname)} không hợp lệ: {exc.msg}.")

    allowed_names = set(FORMULA_VARIABLES.get(fieldname, [])) | set(ALLOWED_FORMULA_FUNCTIONS)
    _validate_formula_ast(compiled.body, allowed_names, fieldname)
    return True


def normalize_formula_tokens(formula, fieldname):
    text = str(formula or "").strip()
    for variable_key in FORMULA_VARIABLES.get(fieldname, []):
        label = VARIABLE_DEFINITIONS[variable_key]["label"]
        text = text.replace(f"[{label}]", variable_key)
    return text


def convert_formula_to_display(formula, fieldname):
    text = str(formula or "").strip()
    for variable_key in sorted(FORMULA_VARIABLES.get(fieldname, []), key=len, reverse=True):
        label = VARIABLE_DEFINITIONS[variable_key]["label"]
        text = text.replace(variable_key, f"[{label}]")
    return text


def _get_variable_meta(variable_key):
    meta = VARIABLE_DEFINITIONS[variable_key]
    return {
        "key": variable_key,
        "label": meta["label"],
        "group": meta["group"],
        "token": f"[{meta['label']}]",
    }


def _group_variables_for_dialog(variables):
    grouped = {}
    for item in variables:
        grouped.setdefault(item["group"], []).append(item)
    return [{"group": group, "items": items} for group, items in grouped.items()]


def _function_label(name):
    labels = {
        "abs": "Trị tuyệt đối",
        "max": "Lấy giá trị lớn hơn",
        "min": "Lấy giá trị nhỏ hơn",
        "round": "Làm tròn số",
    }
    return labels.get(name, name)


def _validate_formula_ast(node, allowed_names, fieldname):
    if isinstance(node, ast.Expression):
        return _validate_formula_ast(node.body, allowed_names, fieldname)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return
        frappe.throw(f"{FORMULA_LABELS.get(fieldname, fieldname)} chỉ hỗ trợ số.")
    if isinstance(node, ast.Name):
        if node.id not in allowed_names:
            frappe.throw(
                f"{FORMULA_LABELS.get(fieldname, fieldname)} đang dùng biến/hàm không được phép: {node.id}."
            )
        return
    if isinstance(node, ast.BinOp):
        if not isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow)):
            frappe.throw(f"{FORMULA_LABELS.get(fieldname, fieldname)} có toán tử không được hỗ trợ.")
        _validate_formula_ast(node.left, allowed_names, fieldname)
        _validate_formula_ast(node.right, allowed_names, fieldname)
        return
    if isinstance(node, ast.UnaryOp):
        if not isinstance(node.op, (ast.UAdd, ast.USub)):
            frappe.throw(f"{FORMULA_LABELS.get(fieldname, fieldname)} có toán tử không được hỗ trợ.")
        _validate_formula_ast(node.operand, allowed_names, fieldname)
        return
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in ALLOWED_FORMULA_FUNCTIONS:
            frappe.throw(f"{FORMULA_LABELS.get(fieldname, fieldname)} chỉ cho phép min, max, abs, round.")
        for arg in node.args:
            _validate_formula_ast(arg, allowed_names, fieldname)
        return
    frappe.throw(f"{FORMULA_LABELS.get(fieldname, fieldname)} có cú pháp không được hỗ trợ.")


def _safe_eval_formula(node, variables):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in ALLOWED_FORMULA_FUNCTIONS:
            return ALLOWED_FORMULA_FUNCTIONS[node.id]
        return flt(variables.get(node.id, 0))
    if isinstance(node, ast.BinOp):
        left = _safe_eval_formula(node.left, variables)
        right = _safe_eval_formula(node.right, variables)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right if right else 0
        if isinstance(node.op, ast.Mod):
            return left % right if right else 0
        if isinstance(node.op, ast.Pow):
            return left**right
    if isinstance(node, ast.UnaryOp):
        value = _safe_eval_formula(node.operand, variables)
        if isinstance(node.op, ast.UAdd):
            return value
        if isinstance(node.op, ast.USub):
            return -value
    if isinstance(node, ast.Call):
        func = _safe_eval_formula(node.func, variables)
        args = [_safe_eval_formula(arg, variables) for arg in node.args]
        return func(*args)
    frappe.throw("Không thể tính công thức lương.")


def get_hourly_rate(contract):
    if flt(contract.standard_working_hours) <= 0:
        frappe.throw("Employee Contract phải có Standard Working Hours lớn hơn 0.")
    return flt(contract.base_salary) / flt(contract.standard_working_hours)


def get_standard_hours_per_day(contract, settings):
    if flt(getattr(contract, "standard_working_hours_per_day", 0)) > 0:
        return flt(contract.standard_working_hours_per_day)
    if 0 < flt(contract.standard_working_hours) <= 24:
        return flt(contract.standard_working_hours)
    return flt(settings.standard_working_hours_per_day) or 8


def get_kpi_metrics(employee, from_date, to_date):
    target_periods = {
        getdate(from_date).strftime("%Y-%m"),
        getdate(from_date).strftime("%m/%Y"),
        str(getdate(from_date)),
    }
    rows = frappe.db.sql(
        """
        select payload_json, posting_date, start_date, end_date
          from `tabPH HRM Record`
         where page_key='hrm-kpi'
           and employee_code=%s
        """,
        (employee,),
        as_dict=True,
    )

    matched = []
    for row in rows:
        payload = frappe.parse_json(row.payload_json) or {}
        period = str(payload.get("kpi_period") or "").strip()
        if period and period in target_periods:
            matched.append(payload)
            continue

        posting_date = row.posting_date or payload.get("posting_date")
        if posting_date and getdate(from_date) <= getdate(posting_date) <= getdate(to_date):
            matched.append(payload)

    if not matched:
        return {"kpi_score": 0, "kpi_achievement_rate": 0}

    scores = [flt(item.get("score")) for item in matched if item.get("score") not in (None, "")]
    rates = [
        flt(item.get("achievement_rate"))
        for item in matched
        if item.get("achievement_rate") not in (None, "")
    ]
    return {
        "kpi_score": (sum(scores) / len(scores)) if scores else 0,
        "kpi_achievement_rate": (sum(rates) / len(rates)) if rates else 0,
    }


def get_employee_default_salary_structure(employee_doc):
    if employee_doc.meta.get_field("default_salary_structure"):
        return employee_doc.get("default_salary_structure")
    return None


def resolve_component_amount(row, base_salary):
    if row.calculation_type == "Percent":
        return flt(base_salary) * flt(row.amount) / 100
    return flt(row.amount)


def ensure_salary_component(component_name, component_type):
    if not component_name or frappe.db.exists("Salary Component", component_name):
        return

    doc = frappe.get_doc(
        {
            "doctype": "Salary Component",
            "salary_component": component_name,
            "salary_component_abbr": frappe.scrub(component_name).upper()[:10],
            "type": component_type,
        }
    )
    doc.insert(ignore_permissions=True)


def _set_if_present(doc, fieldname, value):
    if hasattr(doc, fieldname):
        setattr(doc, fieldname, value)


def ensure_payroll_dependencies(require_salary_slip=True):
    required_doctypes = ["Employee", "Attendance", "Employee Contract"]
    if require_salary_slip:
        required_doctypes.append("Salary Slip")

    missing = [doctype for doctype in required_doctypes if not frappe.db.exists("DocType", doctype)]
    if missing:
        frappe.throw(
            "Thiếu DocType bắt buộc cho Payroll Automation: "
            + ", ".join(missing)
            + ". Hãy cài module HR/Payroll (ví dụ HRMS) rồi migrate lại site."
        )

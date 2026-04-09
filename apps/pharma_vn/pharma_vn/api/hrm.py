import csv
import io
from collections import Counter, defaultdict
from datetime import timedelta
from urllib.parse import urljoin

import frappe
import requests
from frappe.utils import cint, flt, formatdate, get_first_day, get_last_day, getdate
from frappe.utils.data import add_days
from frappe.utils.pdf import get_pdf
from frappe.utils.xlsxutils import make_xlsx, read_xlsx_file_from_attached_file

from pharma_vn.hrm.service import (
    HRM_RECORD_TABLE,
    PAGE_META,
    deserialize_record,
    ensure_hrm_schema,
    get_allowed_page_keys,
    get_record_name,
    normalize_payload,
    validate_page_key,
)


@frappe.whitelist()
def get_page_data(page_key):
    ensure_hrm_schema()
    validate_page_key(page_key)
    if page_key == "hrm-dashboard":
        return {
            "stats": _get_dashboard_stats(),
            "recent_records": _get_recent_records(),
            "reports": _get_module_reports(),
            "pages": [
                {"page_key": key, "label": meta["label"]}
                for key, meta in PAGE_META.items()
                if key != "hrm-dashboard"
            ],
        }
    if page_key == "hrm-reports":
        return {
            "reports": _get_module_reports(),
            "catalog": _get_report_catalog(),
            "meta": PAGE_META[page_key],
        }

    rows = frappe.db.sql(
        f"""
        select name, page_key, title, status, subject, employee_code, employee_name, company,
               posting_date, start_date, end_date, amount, file_url, payload_json, updated_at
          from `{HRM_RECORD_TABLE}`
         where page_key=%s
         order by updated_at desc
         limit 200
        """,
        (page_key,),
        as_dict=True,
    )
    return {
        "records": [deserialize_record(frappe._dict(row)) for row in rows],
        "meta": PAGE_META[page_key],
    }


@frappe.whitelist()
def get_report_data(page_key, report_id, filters=None):
    ensure_hrm_schema()
    validate_page_key(page_key)
    if page_key in {"hrm-dashboard", "hrm-reports"}:
        frappe.throw("Trang này không có report dữ liệu chi tiết.")
    return _build_report_dataset(page_key, report_id, filters)


@frappe.whitelist()
def export_report(page_key, report_id, export_format="xlsx", filters=None):
    ensure_hrm_schema()
    dataset = _build_report_dataset(page_key, report_id, filters)
    export_format = (export_format or "xlsx").lower()
    if export_format not in {"xlsx", "pdf"}:
        frappe.throw("Định dạng export không hợp lệ. Chỉ hỗ trợ XLSX hoặc PDF.")

    rows = []
    rows.append([dataset["title"]])
    if dataset.get("description"):
        rows.append([dataset["description"]])
    rows.append([])
    rows.append([item["label"] for item in dataset.get("summary", [])])
    rows.append([item["value"] for item in dataset.get("summary", [])])
    rows.append([])
    rows.append([column["label"] for column in dataset.get("columns", [])])
    for row in dataset.get("rows", []):
        rows.append([row.get(column["fieldname"], "") for column in dataset.get("columns", [])])

    file_slug = frappe.scrub(f"{page_key}-{report_id}")
    if export_format == "xlsx":
        xlsx_file = make_xlsx(rows, dataset["title"])
        frappe.local.response.filename = f"{file_slug}.xlsx"
        frappe.local.response.filecontent = xlsx_file.getvalue()
        frappe.local.response.type = "binary"
        return

    html = _render_report_pdf_html(dataset)
    frappe.local.response.filename = f"{file_slug}.pdf"
    frappe.local.response.filecontent = get_pdf(html)
    frappe.local.response.type = "pdf"


@frappe.whitelist()
def save_record(page_key, doc):
    ensure_hrm_schema()
    validate_page_key(page_key)
    if page_key == "hrm-dashboard":
        frappe.throw("Dashboard does not support data entry")

    payload = frappe.parse_json(doc) or {}
    record_name = payload.get("name") or get_record_name(page_key)
    normalized = normalize_payload(page_key, payload)
    exists = frappe.db.sql(
        f"select name from `{HRM_RECORD_TABLE}` where name=%s and page_key=%s limit 1",
        (record_name, page_key),
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
            {
                **normalized,
                "name": record_name,
                "page_key": page_key,
                "owner": frappe.session.user,
            },
        )
    else:
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
            {
                **normalized,
                "name": record_name,
                "page_key": page_key,
                "owner": frappe.session.user,
            },
        )

    frappe.db.commit()
    return {
        "name": record_name,
        "records": get_page_data(page_key).get("records", []),
    }


@frappe.whitelist()
def delete_record(page_key, record_name):
    ensure_hrm_schema()
    validate_page_key(page_key)
    frappe.db.sql(
        f"delete from `{HRM_RECORD_TABLE}` where page_key=%s and name=%s",
        (page_key, record_name),
    )
    frappe.db.commit()
    return {"ok": True}


@frappe.whitelist()
def import_attendance_file(file_url):
    ensure_hrm_schema()
    if not file_url:
        frappe.throw("Thiếu file import")

    rows = _read_attendance_rows(file_url)
    payloads = _rows_to_attendance_payloads(rows)
    names = _insert_payloads("hrm-attendance", payloads)
    return {
        "inserted_count": len(names),
        "record_names": names,
        "records": get_page_data("hrm-attendance").get("records", []),
    }


@frappe.whitelist()
def sync_attendance_device(device_config=None):
    ensure_hrm_schema()
    config = frappe.parse_json(device_config) or {}
    ip_address = config.get("ip_address")
    endpoint = config.get("endpoint") or "/api/attendance"
    if not ip_address:
        frappe.throw("Thiếu IP máy chấm công")

    protocol = config.get("protocol") or "http"
    port = config.get("port") or ("443" if protocol == "https" else "80")
    base_url = f"{protocol}://{ip_address}:{port}"
    url = urljoin(f"{base_url}/", endpoint.lstrip("/"))

    headers = {}
    if config.get("auth_token"):
        headers["Authorization"] = f"Bearer {config.get('auth_token')}"

    response = requests.get(url, headers=headers, timeout=flt(config.get("timeout") or 8))
    response.raise_for_status()
    payload = response.json()
    rows = payload.get("records") or payload.get("data") or payload.get("logs") or payload
    if not isinstance(rows, list):
        frappe.throw("Thiết bị không trả về danh sách dữ liệu hợp lệ")

    names = _insert_payloads("hrm-attendance", [_normalize_attendance_row(row) for row in rows if row])
    return {
        "inserted_count": len(names),
        "record_names": names,
        "records": get_page_data("hrm-attendance").get("records", []),
    }


@frappe.whitelist()
def download_attendance_template():
    rows = [
        [
            "employee_code",
            "employee_name",
            "attendance_date",
            "shift_name",
            "check_in",
            "check_out",
            "working_hours",
            "overtime_hours",
            "status",
            "company",
            "notes",
        ],
        [
            "EMP-0001",
            "Nguyen Van A",
            "2026-04-09",
            "Ca sáng",
            "08:00",
            "17:00",
            8,
            0,
            "Submitted",
            "Pharma Vietnam",
            "Import mẫu",
        ],
    ]
    xlsx_file = make_xlsx(rows, "Attendance Template")
    frappe.local.response.filename = "attendance-import-template.xlsx"
    frappe.local.response.filecontent = xlsx_file.getvalue()
    frappe.local.response.type = "binary"


def _get_dashboard_stats():
    stats = []
    totals = frappe.db.sql(
        f"""
        select page_key, count(*) as total, sum(amount) as total_amount
          from `{HRM_RECORD_TABLE}`
         group by page_key
        """,
        as_dict=True,
    )
    totals_map = {row.page_key: row for row in totals}
    for page_key in get_allowed_page_keys():
        row = totals_map.get(page_key)
        stats.append(
            {
                "page_key": page_key,
                "label": PAGE_META[page_key]["label"],
                "total": int(row.total) if row else 0,
                "total_amount": float(row.total_amount or 0) if row else 0,
            }
        )
    return stats


def _get_recent_records():
    rows = frappe.db.sql(
        f"""
        select name, page_key, title, employee_name, status, updated_at
          from `{HRM_RECORD_TABLE}`
         order by updated_at desc
         limit 12
        """,
        as_dict=True,
    )
    return [
        {
            "name": row.name,
            "page_key": row.page_key,
            "label": PAGE_META.get(row.page_key, {}).get("label", row.page_key),
            "title": row.title,
            "employee_name": row.employee_name,
            "status": row.status,
            "updated_at": str(row.updated_at) if row.updated_at else "",
        }
        for row in rows
    ]


def _get_module_reports():
    totals = frappe.db.sql(
        f"""
        select page_key,
               count(*) as total_records,
               sum(amount) as total_amount,
               count(distinct employee_code) as total_employees,
               max(updated_at) as latest_update
          from `{HRM_RECORD_TABLE}`
         group by page_key
        """,
        as_dict=True,
    )
    statuses = frappe.db.sql(
        f"""
        select page_key, status, count(*) as total
          from `{HRM_RECORD_TABLE}`
         where ifnull(status, '') != ''
         group by page_key, status
         order by page_key asc, total desc
        """,
        as_dict=True,
    )
    by_page = {}
    for row in totals:
        by_page[row.page_key] = {
            "page_key": row.page_key,
            "title": PAGE_META.get(row.page_key, {}).get("title", row.page_key),
            "total_records": int(row.total_records or 0),
            "total_employees": int(row.total_employees or 0),
            "total_amount": float(row.total_amount or 0),
            "latest_update": str(row.latest_update) if row.latest_update else "",
            "statuses": [],
        }

    for row in statuses:
        if row.page_key in by_page:
            by_page[row.page_key]["statuses"].append(
                {
                    "status": row.status,
                    "total": int(row.total or 0),
                }
            )

    return [by_page[page_key] for page_key in get_allowed_page_keys() if page_key in by_page]


def _get_report_catalog():
    templates = _get_report_templates()
    reports = _get_module_reports()
    reports_map = {row["page_key"]: row for row in reports}

    output = []
    for page_key in get_allowed_page_keys():
        meta = PAGE_META[page_key]
        report_summary = reports_map.get(
            page_key,
            {
                "total_records": 0,
                "total_employees": 0,
                "total_amount": 0,
                "statuses": [],
                "latest_update": "",
            },
        )
        output.append(
            {
                "page_key": page_key,
                "title": meta["title"],
                "icon": meta["icon"],
                "summary": report_summary,
                "sample_reports": templates.get(page_key, []),
            }
        )
    return output


def _insert_payloads(page_key, payloads):
    names = []
    for payload in payloads:
        if not payload:
            continue
        record_name = get_record_name(page_key)
        normalized = normalize_payload(page_key, payload)
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
            {
                **normalized,
                "name": record_name,
                "page_key": page_key,
                "owner": frappe.session.user,
            },
        )
        names.append(record_name)
    frappe.db.commit()
    return names


def _read_attendance_rows(file_url):
    file_doc = frappe.get_doc("File", {"file_url": file_url})
    file_name = (file_doc.file_name or "").lower()
    if file_name.endswith(".csv"):
        content = file_doc.get_content()
        text = content.decode("utf-8-sig") if isinstance(content, bytes) else content
        return list(csv.reader(io.StringIO(text)))
    if file_name.endswith(".xlsx") or file_name.endswith(".xls"):
        return read_xlsx_file_from_attached_file(file_url=file_url)
    frappe.throw("Chỉ hỗ trợ file CSV hoặc XLSX")


def _rows_to_attendance_payloads(rows):
    if not rows or len(rows) < 2:
        frappe.throw("File import không có dữ liệu")
    headers = [_normalize_header(cell) for cell in rows[0]]
    payloads = []
    for row in rows[1:]:
        if not any(row):
            continue
        payloads.append(
            _normalize_attendance_row(
                {
                    headers[idx]: row[idx] if idx < len(row) else None
                    for idx in range(len(headers))
                    if headers[idx]
                }
            )
        )
    return payloads


def _normalize_attendance_row(row):
    row = frappe._dict(row or {})
    employee_name = row.get("employee_name") or row.get("full_name") or row.get("employee")
    attendance_date = row.get("attendance_date") or row.get("date") or row.get("work_date")
    check_in = row.get("check_in") or row.get("in_time") or row.get("time_in")
    check_out = row.get("check_out") or row.get("out_time") or row.get("time_out")
    return {
        "attendance_title": row.get("attendance_title")
        or row.get("title")
        or f"{employee_name or row.get('employee_code') or 'EMP'} - {attendance_date or frappe.utils.nowdate()}",
        "employee_name": employee_name,
        "employee_code": row.get("employee_code") or row.get("employee_id") or row.get("emp_code"),
        "status": row.get("status") or "Submitted",
        "company": row.get("company"),
        "attendance_date": attendance_date,
        "posting_date": attendance_date,
        "shift_name": row.get("shift_name") or row.get("shift"),
        "check_in": check_in,
        "check_out": check_out,
        "working_hours": row.get("working_hours") or row.get("hours") or row.get("work_hours"),
        "overtime_hours": row.get("overtime_hours") or row.get("ot_hours"),
        "notes": row.get("notes") or row.get("remark") or row.get("remarks"),
        "source": row.get("source") or row.get("device_name") or row.get("machine_name"),
        "device_ip": row.get("device_ip") or row.get("ip_address"),
    }


def _normalize_header(value):
    return (
        str(value or "")
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
    )


def _report_template(report_id, title, description, metrics=None, filters=None):
    return {
        "id": report_id,
        "title": title,
        "description": description,
        "metrics": metrics or [],
        "filters": filters or [],
    }


def _get_report_templates():
    return {
        "hrm-employee-profile": [
            _report_template("employee-status-movement", "Biến động nhân sự theo trạng thái", "Theo dõi số lượng nhân sự theo từng trạng thái để kiểm soát headcount.", ["Tổng nhân sự", "Số trạng thái", "Tỷ lệ active"], ["Tháng", "Phòng ban", "Công ty"]),
            _report_template("employee-by-department", "Danh sách nhân sự theo phòng ban", "Danh sách nhân sự chi tiết theo cơ cấu phòng ban và chức danh.", ["Số nhân sự", "Phòng ban", "Chức danh"], ["Phòng ban", "Công ty", "Trạng thái"]),
            _report_template("birthdays-upcoming", "Nhân sự sắp đến ngày sinh nhật", "Danh sách sinh nhật sắp tới trong 30 ngày tiếp theo.", ["Ngày sinh", "Tuổi mới", "Số năm gắn bó"], ["Tháng", "Phòng ban", "Công ty"]),
            _report_template("probation-ending", "Nhân sự sắp hết thử việc", "Theo dõi nhân sự sắp kết thúc thử việc trong 30 ngày tới.", ["Ngày vào làm", "Ngày hết thử việc", "Số ngày còn lại"], ["Tháng", "Phòng ban", "Công ty"]),
            _report_template("missing-employee-documents", "Danh sách nhân sự thiếu hồ sơ", "Rà soát các trường hồ sơ quan trọng còn thiếu để HR bổ sung.", ["Số trường còn thiếu", "Mức độ hoàn thiện"], ["Phòng ban", "Công ty", "Trạng thái"]),
        ],
        "hrm-contracts": [
            _report_template("contracts-expiring", "Hợp đồng sắp hết hạn", "Danh sách hợp đồng sắp hết hạn trong 60 ngày tới.", ["Số hợp đồng", "Lương thỏa thuận", "Ngày hết hạn"], ["Tháng", "Phòng ban", "Công ty"]),
            _report_template("contract-value-by-type", "Giá trị hợp đồng theo loại", "Tổng hợp số lượng và giá trị hợp đồng theo từng loại.", ["Số lượng", "Tổng lương", "Lương trung bình"], ["Loại hợp đồng", "Công ty"]),
            _report_template("employees-without-active-contract", "Nhân sự chưa có hợp đồng hiệu lực", "Phát hiện nhân sự active nhưng chưa có hợp đồng hiệu lực tại tháng đã chọn.", ["Số nhân sự", "Ngày vào làm", "Phòng ban"], ["Tháng", "Phòng ban", "Công ty"]),
        ],
        "hrm-attendance": [
            _report_template("attendance-monthly-summary", "Tổng hợp công theo tháng", "Tổng hợp công chuẩn, công thực tế, giờ làm và tăng ca theo nhân sự.", ["Công chuẩn", "Công thực tế", "Tăng ca", "Tỷ lệ đi làm"], ["Tháng", "Phòng ban", "Công ty"]),
            _report_template("attendance-late-absent", "Bảng vắng mặt và đi trễ", "Danh sách các ngày vắng mặt, đi trễ hoặc công không đạt.", ["Số ngày vắng", "Số lần đi trễ", "Tổng phút đi trễ"], ["Tháng", "Phòng ban", "Nhân sự"]),
            _report_template("attendance-overtime", "Thống kê tăng ca theo nhân viên", "Tổng hợp số giờ tăng ca và số ngày có tăng ca.", ["Giờ tăng ca", "Ngày tăng ca", "Số nhân sự có OT"], ["Tháng", "Phòng ban", "Công ty"]),
        ],
        "hrm-leave": [
            _report_template("leave-by-status", "Đơn nghỉ theo trạng thái", "Theo dõi đơn nghỉ theo trạng thái và tổng số ngày nghỉ.", ["Số đơn", "Số ngày nghỉ", "Tỷ lệ duyệt"], ["Tháng", "Phòng ban", "Công ty"]),
            _report_template("leave-days-by-employee", "Tổng ngày nghỉ theo nhân viên", "Tổng hợp số ngày nghỉ theo từng nhân viên trong tháng.", ["Số ngày nghỉ", "Số đơn", "Loại nghỉ"], ["Tháng", "Phòng ban", "Công ty"]),
            _report_template("leave-calendar-by-department", "Lịch nghỉ theo phòng ban", "Danh sách nghỉ phép chi tiết để điều phối nhân sự theo phòng ban.", ["Số người nghỉ", "Loại nghỉ", "Thời gian nghỉ"], ["Tháng", "Phòng ban", "Công ty"]),
        ],
        "hrm-payroll": [
            _report_template("payroll-monthly-fund", "Tổng quỹ lương theo tháng", "Tổng hợp bảng lương chi tiết theo kỳ lương và nhân sự.", ["Lương cơ bản", "Phụ cấp", "Khấu trừ", "Thực lĩnh"], ["Tháng", "Phòng ban", "Công ty"]),
            _report_template("payroll-top-net", "Top lương thực lĩnh", "Xếp hạng nhân sự có thực lĩnh cao nhất trong tháng.", ["Thực lĩnh", "Khấu trừ", "Lương hợp đồng"], ["Tháng", "Phòng ban", "Công ty"]),
            _report_template("payroll-deductions", "Phân tích khấu trừ và BHXH", "Phân tích tỷ lệ khấu trừ trên từng bảng lương.", ["Khấu trừ", "Tỷ lệ khấu trừ", "Thực lĩnh"], ["Tháng", "Phòng ban", "Công ty"]),
        ],
        "hrm-performance": [
            _report_template("performance-cycle-results", "Kết quả đánh giá theo kỳ", "Kết quả đánh giá chi tiết theo kỳ và xếp loại.", ["Điểm trung bình", "Xếp loại", "Phiếu hoàn tất"], ["Kỳ đánh giá", "Phòng ban", "Công ty"]),
            _report_template("performance-improvement-needed", "Danh sách nhân sự cần cải thiện", "Tập trung vào các nhân sự có điểm đánh giá thấp hoặc đang review.", ["Điểm thấp", "Phiếu chưa hoàn tất", "Kế hoạch cải thiện"], ["Kỳ đánh giá", "Phòng ban", "Công ty"]),
            _report_template("performance-completion-rate", "Tỷ lệ hoàn thành đánh giá", "Theo dõi tỷ lệ hoàn thành đánh giá theo phòng ban.", ["Tổng phiếu", "Phiếu hoàn tất", "Tỷ lệ hoàn thành"], ["Kỳ đánh giá", "Phòng ban", "Công ty"]),
        ],
        "hrm-kpi": [
            _report_template("kpi-completion-rate", "Tỷ lệ hoàn thành KPI theo kỳ", "Tổng hợp mức độ hoàn thành KPI theo từng nhân sự.", ["Tỷ lệ hoàn thành", "KPI đạt", "KPI chưa đạt"], ["Kỳ KPI", "Phòng ban", "Công ty"]),
            _report_template("kpi-top-employee", "Nhân sự có KPI cao nhất", "Xếp hạng nhân sự có achievement rate cao nhất.", ["Top KPI", "Achievement rate", "Trọng số"], ["Kỳ KPI", "Phòng ban", "Công ty"]),
            _report_template("kpi-goal-by-department", "Mục tiêu KPI theo phòng ban", "So sánh mục tiêu và kết quả KPI theo phòng ban.", ["Target", "Actual", "Achievement"], ["Kỳ KPI", "Phòng ban", "Công ty"]),
        ],
        "hrm-meeting-room-booking": [
            _report_template("meeting-room-utilization", "Tần suất sử dụng phòng họp", "Tổng hợp số lượt đặt và tổng giờ sử dụng theo phòng.", ["Số lượt đặt", "Tổng giờ", "Tỷ lệ sử dụng"], ["Tháng", "Phòng họp", "Công ty"]),
            _report_template("meeting-room-weekly-schedule", "Lịch đặt phòng theo tuần", "Xem lịch đặt phòng chi tiết trong tháng đã chọn.", ["Ngày họp", "Khung giờ", "Người đặt"], ["Tháng", "Phòng họp", "Công ty"]),
            _report_template("meeting-room-top-rooms", "Phòng họp được dùng nhiều nhất", "Xếp hạng phòng họp theo mức sử dụng.", ["Số lượt đặt", "Tổng giờ", "Số người tham dự"], ["Tháng", "Công ty"]),
        ],
        "hrm-document-archive": [
            _report_template("document-stock-by-type", "Tồn kho hồ sơ theo loại", "Thống kê số lượng hồ sơ theo loại và vị trí lưu trữ.", ["Số hồ sơ", "Loại hồ sơ", "Vị trí lưu"], ["Loại hồ sơ", "Công ty"]),
            _report_template("documents-expiring", "Hồ sơ sắp hết hạn lưu trữ", "Danh sách hồ sơ gần đến hạn lưu trữ trong 60 ngày tới.", ["Ngày hết hạn", "Loại hồ sơ", "Nhân sự liên quan"], ["Tháng", "Loại hồ sơ", "Công ty"]),
            _report_template("employees-missing-required-documents", "Nhân sự thiếu hồ sơ bắt buộc", "Đối soát nhân sự với kho hồ sơ để tìm giấy tờ bắt buộc còn thiếu.", ["Số hồ sơ thiếu", "Nhân sự thiếu hồ sơ", "Phòng ban"], ["Phòng ban", "Công ty"]),
        ],
        "hrm-offboarding": [
            _report_template("offboarding-open-cases", "Quy trình nghỉ việc đang mở", "Theo dõi hồ sơ nghỉ việc chưa hoàn tất để không sót checklist.", ["Số hồ sơ mở", "Ngày làm cuối", "Người bàn giao"], ["Tháng", "Phòng ban", "Công ty"]),
            _report_template("offboarding-monthly-trend", "Thống kê nghỉ việc theo tháng", "Thống kê số lượng nghỉ việc và quyết toán theo tháng.", ["Số hồ sơ", "Quyết toán", "Tỷ lệ hoàn tất"], ["Năm", "Phòng ban", "Công ty"]),
            _report_template("offboarding-missing-checklist", "Checklist bàn giao còn thiếu", "Liệt kê các hồ sơ nghỉ việc còn thiếu bước bàn giao hoặc quyết toán.", ["Bước còn thiếu", "Tài sản/chứng từ", "Ngày làm cuối"], ["Phòng ban", "Công ty", "Trạng thái"]),
        ],
    }


def _build_report_dataset(page_key, report_id, filters=None):
    templates = _get_report_templates()
    template = next((item for item in templates.get(page_key, []) if item["id"] == report_id), None)
    if not template:
        frappe.throw("Không tìm thấy mẫu report được chọn.")

    normalized_filters = frappe.parse_json(filters) if isinstance(filters, str) else (filters or {})
    builder = {
        "hrm-employee-profile": _build_employee_report,
        "hrm-contracts": _build_contract_report,
        "hrm-attendance": _build_attendance_report,
        "hrm-leave": _build_leave_report,
        "hrm-payroll": _build_payroll_report,
        "hrm-performance": _build_performance_report,
        "hrm-kpi": _build_kpi_report,
        "hrm-meeting-room-booking": _build_meeting_room_report,
        "hrm-document-archive": _build_document_report,
        "hrm-offboarding": _build_offboarding_report,
    }.get(page_key)
    dataset = builder(report_id, normalized_filters, template)
    dataset["report_id"] = report_id
    dataset["page_key"] = page_key
    dataset["filters"] = normalized_filters
    return dataset


def _build_employee_report(report_id, filters, template):
    records = _apply_common_filters(_get_records("hrm-employee-profile"), filters)
    today = _get_filter_month(filters)
    base_date = getdate(today)
    if report_id == "employee-status-movement":
        counts = Counter((row.get("status") or "Chưa cập nhật") for row in records)
        rows = [{"status": status, "employee_count": total} for status, total in sorted(counts.items())]
        return _dataset(
            template,
            [("status", "Trạng thái", "Data"), ("employee_count", "Số nhân sự", "Int")],
            rows,
            [
                _summary("Tổng nhân sự", len(records), "Int"),
                _summary("Số trạng thái", len(rows), "Int"),
                _summary("Tỷ lệ Active", _ratio_percent(counts.get("Active", 0), len(records)), "Percent"),
            ],
        )
    if report_id == "employee-by-department":
        rows = [
            {
                "department": row.get("department") or "Chưa phân bổ",
                "employee_name": row.get("employee_name") or row.get("full_name"),
                "employee_code": row.get("employee_code"),
                "designation": row.get("designation"),
                "join_date": row.get("join_date") or row.get("start_date"),
                "status": row.get("status"),
            }
            for row in records
        ]
        rows.sort(key=lambda item: ((item["department"] or ""), (item["employee_name"] or "")))
        return _dataset(
            template,
            [("department", "Phòng ban", "Data"), ("employee_name", "Nhân sự", "Data"), ("employee_code", "Mã nhân sự", "Data"), ("designation", "Chức danh", "Data"), ("join_date", "Ngày vào làm", "Date"), ("status", "Trạng thái", "Data")],
            rows,
            [_summary("Số phòng ban", len({row.get("department") or "Chưa phân bổ" for row in records}), "Int"), _summary("Tổng nhân sự", len(records), "Int")],
        )
    if report_id == "birthdays-upcoming":
        rows = []
        end_date = add_days(base_date, 30)
        for row in records:
            birth_date = _parse_date(row.get("date_of_birth"))
            if not birth_date:
                continue
            next_birthday = birth_date.replace(year=base_date.year)
            if next_birthday < base_date:
                next_birthday = next_birthday.replace(year=base_date.year + 1)
            if next_birthday > end_date:
                continue
            rows.append(
                {
                    "employee_name": row.get("employee_name") or row.get("full_name"),
                    "department": row.get("department"),
                    "birthday": next_birthday.isoformat(),
                    "turning_age": max(next_birthday.year - birth_date.year, 0),
                    "tenure_years": _year_delta(row.get("join_date") or row.get("start_date"), next_birthday),
                }
            )
        rows.sort(key=lambda item: item["birthday"])
        return _dataset(
            template,
            [("employee_name", "Nhân sự", "Data"), ("department", "Phòng ban", "Data"), ("birthday", "Sinh nhật", "Date"), ("turning_age", "Tuổi mới", "Int"), ("tenure_years", "Thâm niên (năm)", "Float")],
            rows,
            [_summary("Nhân sự sắp sinh nhật", len(rows), "Int"), _summary("Khung thời gian", "30 ngày tới", "Data")],
        )
    if report_id == "probation-ending":
        rows = []
        end_date = add_days(base_date, 30)
        for row in records:
            join_date = _parse_date(row.get("join_date") or row.get("start_date"))
            if not join_date:
                continue
            probation_end = add_days(join_date, cint(row.get("probation_days") or 60))
            if probation_end < base_date or probation_end > end_date:
                continue
            rows.append(
                {
                    "employee_name": row.get("employee_name") or row.get("full_name"),
                    "department": row.get("department"),
                    "join_date": join_date.isoformat(),
                    "probation_end": probation_end.isoformat(),
                    "days_left": max((probation_end - base_date).days, 0),
                    "status": row.get("status"),
                }
            )
        rows.sort(key=lambda item: item["probation_end"])
        return _dataset(
            template,
            [("employee_name", "Nhân sự", "Data"), ("department", "Phòng ban", "Data"), ("join_date", "Ngày vào làm", "Date"), ("probation_end", "Ngày hết thử việc", "Date"), ("days_left", "Còn lại (ngày)", "Int"), ("status", "Trạng thái", "Data")],
            rows,
            [_summary("Nhân sự sắp hết thử việc", len(rows), "Int")],
        )

    required_fields = {"email": "Email", "phone": "Điện thoại", "id_number": "CCCD", "bank_account": "Tài khoản ngân hàng", "emergency_contact": "Liên hệ khẩn cấp"}
    rows = []
    for row in records:
        missing = [label for fieldname, label in required_fields.items() if not row.get(fieldname)]
        if not missing:
            continue
        completion = round(((len(required_fields) - len(missing)) / len(required_fields)) * 100, 1)
        rows.append(
            {
                "employee_name": row.get("employee_name") or row.get("full_name"),
                "department": row.get("department"),
                "missing_fields": ", ".join(missing),
                "missing_count": len(missing),
                "completion_rate": completion,
                "status": row.get("status"),
            }
        )
    rows.sort(key=lambda item: (-item["missing_count"], item["employee_name"] or ""))
    return _dataset(
        template,
        [("employee_name", "Nhân sự", "Data"), ("department", "Phòng ban", "Data"), ("missing_fields", "Hồ sơ còn thiếu", "Data"), ("missing_count", "Số trường thiếu", "Int"), ("completion_rate", "Hoàn thiện (%)", "Percent"), ("status", "Trạng thái", "Data")],
        rows,
        [_summary("Nhân sự thiếu hồ sơ", len(rows), "Int"), _summary("Tỷ lệ hoàn thiện TB", _average([row["completion_rate"] for row in rows]), "Percent")],
    )


def _build_contract_report(report_id, filters, template):
    employee_map = _get_employee_map()
    records = _apply_common_filters(_get_records("hrm-contracts"), filters, employee_map)
    base_date = getdate(_get_filter_month(filters))
    if report_id == "contracts-expiring":
        end_window = add_days(base_date, 60)
        rows = []
        for row in records:
            contract_end = _parse_date(row.get("contract_end") or row.get("end_date"))
            if not contract_end or contract_end < base_date or contract_end > end_window:
                continue
            profile = employee_map.get(row.get("employee_code"), {})
            rows.append(
                {
                    "contract_title": row.get("contract_title") or row.get("title"),
                    "employee_name": row.get("employee_name"),
                    "department": profile.get("department"),
                    "contract_type": row.get("contract_type"),
                    "contract_end": contract_end.isoformat(),
                    "salary_amount": flt(row.get("salary_amount")),
                    "days_left": (contract_end - base_date).days,
                }
            )
        rows.sort(key=lambda item: item["contract_end"])
        return _dataset(template, [("contract_title", "Hợp đồng", "Data"), ("employee_name", "Nhân sự", "Data"), ("department", "Phòng ban", "Data"), ("contract_type", "Loại hợp đồng", "Data"), ("contract_end", "Hết hạn", "Date"), ("salary_amount", "Lương thỏa thuận", "Currency"), ("days_left", "Còn lại (ngày)", "Int")], rows, [_summary("Hợp đồng sắp hết hạn", len(rows), "Int"), _summary("Tổng giá trị", sum(flt(row["salary_amount"]) for row in rows), "Currency")])
    if report_id == "contract-value-by-type":
        grouped = defaultdict(lambda: {"contract_count": 0, "total_salary": 0.0})
        for row in records:
            key = row.get("contract_type") or "Chưa phân loại"
            grouped[key]["contract_count"] += 1
            grouped[key]["total_salary"] += flt(row.get("salary_amount"))
        rows = []
        for key, item in grouped.items():
            rows.append({"contract_type": key, "contract_count": item["contract_count"], "total_salary": item["total_salary"], "average_salary": item["total_salary"] / item["contract_count"] if item["contract_count"] else 0})
        rows.sort(key=lambda item: -item["total_salary"])
        return _dataset(template, [("contract_type", "Loại hợp đồng", "Data"), ("contract_count", "Số lượng", "Int"), ("total_salary", "Tổng lương", "Currency"), ("average_salary", "Lương trung bình", "Currency")], rows, [_summary("Tổng loại hợp đồng", len(rows), "Int"), _summary("Tổng giá trị", sum(item["total_salary"] for item in rows), "Currency")])

    employee_records = _apply_common_filters(_get_records("hrm-employee-profile"), filters)
    month_date = getdate(_get_filter_month(filters))
    rows = []
    for employee in employee_records:
        active_contract = False
        for contract in records:
            if contract.get("employee_code") != employee.get("employee_code"):
                continue
            start_date = _parse_date(contract.get("contract_start") or contract.get("start_date"))
            end_date = _parse_date(contract.get("contract_end") or contract.get("end_date"))
            if start_date and month_date < start_date:
                continue
            if end_date and month_date > end_date:
                continue
            if (contract.get("status") or "").lower() in {"active", "submitted"}:
                active_contract = True
                break
        if not active_contract:
            rows.append({"employee_name": employee.get("employee_name") or employee.get("full_name"), "employee_code": employee.get("employee_code"), "department": employee.get("department"), "designation": employee.get("designation"), "join_date": employee.get("join_date") or employee.get("start_date"), "status": employee.get("status")})
    rows.sort(key=lambda item: (item["department"] or "", item["employee_name"] or ""))
    return _dataset(template, [("employee_name", "Nhân sự", "Data"), ("employee_code", "Mã nhân sự", "Data"), ("department", "Phòng ban", "Data"), ("designation", "Chức danh", "Data"), ("join_date", "Ngày vào làm", "Date"), ("status", "Trạng thái", "Data")], rows, [_summary("Nhân sự thiếu hợp đồng hiệu lực", len(rows), "Int")])


def _build_attendance_report(report_id, filters, template):
    employee_map = _get_employee_map()
    records = _filter_by_month(_apply_common_filters(_get_records("hrm-attendance"), filters, employee_map), filters, ("attendance_date", "posting_date"))
    month_date = getdate(_get_filter_month(filters))
    standard_days = _working_days_in_month(month_date.year, month_date.month)
    if report_id == "attendance-monthly-summary":
        grouped = defaultdict(lambda: {"employee_name": "", "department": "", "actual_days": 0, "absent_days": 0, "working_hours": 0.0, "overtime_hours": 0.0})
        for row in records:
            key = row.get("employee_code") or row.get("employee_name")
            profile = employee_map.get(row.get("employee_code"), {})
            grouped[key]["employee_name"] = row.get("employee_name") or key
            grouped[key]["department"] = profile.get("department")
            if (row.get("status") or "").lower() == "submitted" and flt(row.get("working_hours")) > 0:
                grouped[key]["actual_days"] += 1
            else:
                grouped[key]["absent_days"] += 1
            grouped[key]["working_hours"] += flt(row.get("working_hours"))
            grouped[key]["overtime_hours"] += flt(row.get("overtime_hours"))
        rows = []
        for item in grouped.values():
            item["standard_days"] = standard_days
            item["attendance_rate"] = round((item["actual_days"] / standard_days) * 100, 1) if standard_days else 0
            rows.append(item)
        rows.sort(key=lambda item: (-item["actual_days"], item["employee_name"]))
        return _dataset(template, [("employee_name", "Nhân sự", "Data"), ("department", "Phòng ban", "Data"), ("standard_days", "Công chuẩn", "Int"), ("actual_days", "Công thực tế", "Int"), ("absent_days", "Thiếu công", "Int"), ("working_hours", "Giờ làm", "Float"), ("overtime_hours", "Tăng ca", "Float"), ("attendance_rate", "Đi làm (%)", "Percent")], rows, [_summary("Tổng nhân sự có công", len(rows), "Int"), _summary("Công chuẩn tháng", standard_days, "Int"), _summary("Tổng giờ tăng ca", sum(item["overtime_hours"] for item in rows), "Float")])
    if report_id == "attendance-late-absent":
        rows = []
        for row in records:
            issues = []
            check_in = row.get("check_in") or ""
            if (row.get("status") or "").lower() != "submitted" or flt(row.get("working_hours")) <= 0:
                issues.append("Vắng mặt")
            if check_in and check_in > "08:15":
                issues.append("Đi trễ")
            if flt(row.get("working_hours")) and flt(row.get("working_hours")) < 8:
                issues.append("Thiếu giờ")
            if not issues:
                continue
            profile = employee_map.get(row.get("employee_code"), {})
            rows.append({"attendance_date": row.get("attendance_date") or row.get("posting_date"), "employee_name": row.get("employee_name"), "department": profile.get("department"), "check_in": check_in, "working_hours": flt(row.get("working_hours")), "issue": ", ".join(issues), "status": row.get("status")})
        rows.sort(key=lambda item: (item["attendance_date"] or "", item["employee_name"] or ""))
        return _dataset(template, [("attendance_date", "Ngày công", "Date"), ("employee_name", "Nhân sự", "Data"), ("department", "Phòng ban", "Data"), ("check_in", "Giờ vào", "Data"), ("working_hours", "Giờ làm", "Float"), ("issue", "Cảnh báo", "Data"), ("status", "Trạng thái", "Data")], rows, [_summary("Tổng cảnh báo", len(rows), "Int"), _summary("Số ngày vắng", len([row for row in rows if "Vắng mặt" in row["issue"]]), "Int")])

    grouped = defaultdict(lambda: {"employee_name": "", "department": "", "overtime_hours": 0.0, "overtime_days": 0})
    for row in records:
        overtime = flt(row.get("overtime_hours"))
        if overtime <= 0:
            continue
        key = row.get("employee_code") or row.get("employee_name")
        profile = employee_map.get(row.get("employee_code"), {})
        grouped[key]["employee_name"] = row.get("employee_name") or key
        grouped[key]["department"] = profile.get("department")
        grouped[key]["overtime_hours"] += overtime
        grouped[key]["overtime_days"] += 1
    rows = list(grouped.values())
    rows.sort(key=lambda item: (-item["overtime_hours"], item["employee_name"]))
    return _dataset(template, [("employee_name", "Nhân sự", "Data"), ("department", "Phòng ban", "Data"), ("overtime_days", "Ngày tăng ca", "Int"), ("overtime_hours", "Giờ tăng ca", "Float")], rows, [_summary("Nhân sự có tăng ca", len(rows), "Int"), _summary("Tổng giờ tăng ca", sum(item["overtime_hours"] for item in rows), "Float")])


def _build_leave_report(report_id, filters, template):
    employee_map = _get_employee_map()
    records = _filter_by_month(_apply_common_filters(_get_records("hrm-leave"), filters, employee_map), filters, ("start_date", "posting_date"))
    if report_id == "leave-by-status":
        grouped = defaultdict(lambda: {"leave_count": 0, "total_days": 0.0})
        for row in records:
            key = row.get("status") or "Chưa cập nhật"
            grouped[key]["leave_count"] += 1
            grouped[key]["total_days"] += flt(row.get("total_days"))
        rows = [{"status": key, "leave_count": item["leave_count"], "total_days": item["total_days"]} for key, item in grouped.items()]
        rows.sort(key=lambda item: -item["leave_count"])
        approved_days = sum(item["total_days"] for item in rows if item["status"] == "Approved")
        return _dataset(template, [("status", "Trạng thái", "Data"), ("leave_count", "Số đơn", "Int"), ("total_days", "Số ngày nghỉ", "Float")], rows, [_summary("Tổng đơn nghỉ", sum(item["leave_count"] for item in rows), "Int"), _summary("Ngày nghỉ đã duyệt", approved_days, "Float")])
    if report_id == "leave-days-by-employee":
        grouped = defaultdict(lambda: {"employee_name": "", "department": "", "leave_count": 0, "total_days": 0.0})
        for row in records:
            key = row.get("employee_code") or row.get("employee_name")
            profile = employee_map.get(row.get("employee_code"), {})
            grouped[key]["employee_name"] = row.get("employee_name") or key
            grouped[key]["department"] = profile.get("department")
            grouped[key]["leave_count"] += 1
            grouped[key]["total_days"] += flt(row.get("total_days"))
        rows = list(grouped.values())
        rows.sort(key=lambda item: (-item["total_days"], item["employee_name"]))
        return _dataset(template, [("employee_name", "Nhân sự", "Data"), ("department", "Phòng ban", "Data"), ("leave_count", "Số đơn", "Int"), ("total_days", "Tổng ngày nghỉ", "Float")], rows, [_summary("Nhân sự có đơn nghỉ", len(rows), "Int"), _summary("Tổng ngày nghỉ", sum(item["total_days"] for item in rows), "Float")])

    rows = []
    for row in records:
        profile = employee_map.get(row.get("employee_code"), {})
        rows.append({"department": profile.get("department"), "employee_name": row.get("employee_name"), "leave_type": row.get("leave_type"), "start_date": row.get("start_date"), "end_date": row.get("end_date"), "total_days": flt(row.get("total_days")), "status": row.get("status")})
    rows.sort(key=lambda item: (item["start_date"] or "", item["department"] or ""))
    return _dataset(template, [("department", "Phòng ban", "Data"), ("employee_name", "Nhân sự", "Data"), ("leave_type", "Loại nghỉ", "Data"), ("start_date", "Từ ngày", "Date"), ("end_date", "Đến ngày", "Date"), ("total_days", "Số ngày", "Float"), ("status", "Trạng thái", "Data")], rows, [_summary("Lịch nghỉ", len(rows), "Int")])


def _build_payroll_report(report_id, filters, template):
    employee_map = _get_employee_map()
    records = _filter_by_month(_apply_common_filters(_get_records("hrm-payroll"), filters, employee_map), filters, ("pay_period", "posting_date", "start_date"))
    for row in records:
        row["department"] = employee_map.get(row.get("employee_code"), {}).get("department")
    if report_id == "payroll-monthly-fund":
        rows = [
            {
                "employee_name": row.get("employee_name"),
                "department": row.get("department"),
                "pay_period": row.get("pay_period") or row.get("start_date"),
                "base_salary": flt(row.get("base_salary")),
                "allowance_amount": flt(row.get("allowance_amount")),
                "deduction_amount": flt(row.get("deduction_amount")),
                "net_salary": flt(row.get("net_salary")),
                "status": row.get("status"),
            }
            for row in records
        ]
        rows.sort(key=lambda item: (-item["net_salary"], item["employee_name"] or ""))
        return _dataset(template, [("employee_name", "Nhân sự", "Data"), ("department", "Phòng ban", "Data"), ("pay_period", "Kỳ lương", "Data"), ("base_salary", "Lương cơ bản", "Currency"), ("allowance_amount", "Phụ cấp", "Currency"), ("deduction_amount", "Khấu trừ", "Currency"), ("net_salary", "Thực lĩnh", "Currency"), ("status", "Trạng thái", "Data")], rows, [_summary("Tổng bảng lương", len(rows), "Int"), _summary("Tổng thực lĩnh", sum(item["net_salary"] for item in rows), "Currency"), _summary("Tổng khấu trừ", sum(item["deduction_amount"] for item in rows), "Currency")])
    if report_id == "payroll-top-net":
        rows = sorted(
            [
                {"employee_name": row.get("employee_name"), "department": row.get("department"), "base_salary": flt(row.get("base_salary")), "deduction_amount": flt(row.get("deduction_amount")), "net_salary": flt(row.get("net_salary")), "status": row.get("status")}
                for row in records
            ],
            key=lambda item: (-item["net_salary"], item["employee_name"] or ""),
        )[:10]
        return _dataset(template, [("employee_name", "Nhân sự", "Data"), ("department", "Phòng ban", "Data"), ("base_salary", "Lương hợp đồng", "Currency"), ("deduction_amount", "Khấu trừ", "Currency"), ("net_salary", "Thực lĩnh", "Currency"), ("status", "Trạng thái", "Data")], rows, [_summary("Top nhân sự", len(rows), "Int"), _summary("Thực lĩnh cao nhất", rows[0]["net_salary"] if rows else 0, "Currency")])

    rows = []
    for row in records:
        base_salary = flt(row.get("base_salary"))
        deduction = flt(row.get("deduction_amount"))
        rows.append({"employee_name": row.get("employee_name"), "department": row.get("department"), "base_salary": base_salary, "deduction_amount": deduction, "deduction_rate": round((deduction / base_salary) * 100, 1) if base_salary else 0, "net_salary": flt(row.get("net_salary")), "status": row.get("status")})
    rows.sort(key=lambda item: (-item["deduction_rate"], item["employee_name"] or ""))
    return _dataset(template, [("employee_name", "Nhân sự", "Data"), ("department", "Phòng ban", "Data"), ("base_salary", "Lương cơ bản", "Currency"), ("deduction_amount", "Khấu trừ", "Currency"), ("deduction_rate", "Tỷ lệ khấu trừ (%)", "Percent"), ("net_salary", "Thực lĩnh", "Currency"), ("status", "Trạng thái", "Data")], rows, [_summary("Tổng bảng lương", len(rows), "Int"), _summary("Khấu trừ TB", _average([item["deduction_rate"] for item in rows]), "Percent")])


def _build_performance_report(report_id, filters, template):
    employee_map = _get_employee_map()
    records = _apply_common_filters(_get_records("hrm-performance"), filters, employee_map)
    period = (filters or {}).get("month")
    if period:
        period = str(period)[:7]
        records = [row for row in records if str(row.get("review_period") or "").startswith(period)]
    if report_id == "performance-cycle-results":
        rows = []
        for row in records:
            score = flt(row.get("score"))
            rows.append({"employee_name": row.get("employee_name"), "department": employee_map.get(row.get("employee_code"), {}).get("department"), "review_period": row.get("review_period"), "reviewer": row.get("reviewer"), "score": score, "rank": _score_rank(score), "status": row.get("status")})
        rows.sort(key=lambda item: (-item["score"], item["employee_name"] or ""))
        return _dataset(template, [("employee_name", "Nhân sự", "Data"), ("department", "Phòng ban", "Data"), ("review_period", "Kỳ", "Data"), ("reviewer", "Người đánh giá", "Data"), ("score", "Điểm", "Float"), ("rank", "Xếp loại", "Data"), ("status", "Trạng thái", "Data")], rows, [_summary("Phiếu đánh giá", len(rows), "Int"), _summary("Điểm trung bình", _average([item["score"] for item in rows]), "Float")])
    if report_id == "performance-improvement-needed":
        rows = []
        for row in records:
            score = flt(row.get("score"))
            if score >= 70 and row.get("status") == "Completed":
                continue
            rows.append({"employee_name": row.get("employee_name"), "department": employee_map.get(row.get("employee_code"), {}).get("department"), "review_period": row.get("review_period"), "score": score, "status": row.get("status"), "improvement_plan": row.get("improvement_plan") or "Chưa cập nhật"})
        rows.sort(key=lambda item: (item["score"], item["employee_name"] or ""))
        return _dataset(template, [("employee_name", "Nhân sự", "Data"), ("department", "Phòng ban", "Data"), ("review_period", "Kỳ", "Data"), ("score", "Điểm", "Float"), ("status", "Trạng thái", "Data"), ("improvement_plan", "Kế hoạch cải thiện", "Data")], rows, [_summary("Nhân sự cần cải thiện", len(rows), "Int")])

    grouped = defaultdict(lambda: {"total": 0, "completed": 0})
    for row in records:
        department = employee_map.get(row.get("employee_code"), {}).get("department") or "Chưa phân bổ"
        grouped[department]["total"] += 1
        if row.get("status") == "Completed":
            grouped[department]["completed"] += 1
    rows = []
    for department, item in grouped.items():
        rows.append({"department": department, "total_reviews": item["total"], "completed_reviews": item["completed"], "completion_rate": round((item["completed"] / item["total"]) * 100, 1) if item["total"] else 0})
    rows.sort(key=lambda item: -item["completion_rate"])
    return _dataset(template, [("department", "Phòng ban", "Data"), ("total_reviews", "Tổng phiếu", "Int"), ("completed_reviews", "Đã hoàn tất", "Int"), ("completion_rate", "Hoàn thành (%)", "Percent")], rows, [_summary("Phòng ban có đánh giá", len(rows), "Int"), _summary("Tỷ lệ hoàn thành TB", _average([item["completion_rate"] for item in rows]), "Percent")])


def _build_kpi_report(report_id, filters, template):
    employee_map = _get_employee_map()
    records = _apply_common_filters(_get_records("hrm-kpi"), filters, employee_map)
    period = (filters or {}).get("month")
    if period:
        period = str(period)[:7]
        records = [row for row in records if str(row.get("kpi_period") or "").startswith(period)]
    if report_id == "kpi-completion-rate":
        rows = []
        for row in records:
            rows.append({"employee_name": row.get("employee_name"), "department": employee_map.get(row.get("employee_code"), {}).get("department"), "kpi_period": row.get("kpi_period"), "achievement_rate": flt(row.get("achievement_rate")), "weight": flt(row.get("weight")), "status": row.get("status")})
        rows.sort(key=lambda item: (-item["achievement_rate"], item["employee_name"] or ""))
        return _dataset(template, [("employee_name", "Nhân sự", "Data"), ("department", "Phòng ban", "Data"), ("kpi_period", "Kỳ KPI", "Data"), ("achievement_rate", "Hoàn thành (%)", "Percent"), ("weight", "Trọng số", "Float"), ("status", "Trạng thái", "Data")], rows, [_summary("KPI đang theo dõi", len(rows), "Int"), _summary("Achievement TB", _average([item["achievement_rate"] for item in rows]), "Percent")])
    if report_id == "kpi-top-employee":
        rows = sorted(
            [
                {"employee_name": row.get("employee_name"), "department": employee_map.get(row.get("employee_code"), {}).get("department"), "kpi_title": row.get("kpi_title"), "achievement_rate": flt(row.get("achievement_rate")), "weight": flt(row.get("weight")), "status": row.get("status")}
                for row in records
            ],
            key=lambda item: (-item["achievement_rate"], item["employee_name"] or ""),
        )[:10]
        return _dataset(template, [("employee_name", "Nhân sự", "Data"), ("department", "Phòng ban", "Data"), ("kpi_title", "KPI", "Data"), ("achievement_rate", "Hoàn thành (%)", "Percent"), ("weight", "Trọng số", "Float"), ("status", "Trạng thái", "Data")], rows, [_summary("Top KPI", len(rows), "Int"), _summary("Achievement cao nhất", rows[0]["achievement_rate"] if rows else 0, "Percent")])

    grouped = defaultdict(lambda: {"target_total": 0.0, "actual_total": 0.0, "achievement_rates": []})
    for row in records:
        department = employee_map.get(row.get("employee_code"), {}).get("department") or "Chưa phân bổ"
        grouped[department]["target_total"] += flt(row.get("target_value"))
        grouped[department]["actual_total"] += flt(row.get("actual_value"))
        grouped[department]["achievement_rates"].append(flt(row.get("achievement_rate")))
    rows = []
    for department, item in grouped.items():
        rows.append({"department": department, "target_total": item["target_total"], "actual_total": item["actual_total"], "achievement_rate": _average(item["achievement_rates"])})
    rows.sort(key=lambda item: -item["achievement_rate"])
    return _dataset(template, [("department", "Phòng ban", "Data"), ("target_total", "Mục tiêu", "Float"), ("actual_total", "Kết quả", "Float"), ("achievement_rate", "Hoàn thành (%)", "Percent")], rows, [_summary("Phòng ban có KPI", len(rows), "Int"), _summary("Achievement TB", _average([item["achievement_rate"] for item in rows]), "Percent")])


def _build_meeting_room_report(report_id, filters, template):
    records = _filter_by_month(_apply_common_filters(_get_records("hrm-meeting-room-booking"), filters), filters, ("booking_date", "posting_date"))
    if report_id == "meeting-room-weekly-schedule":
        rows = []
        for row in records:
            rows.append({"booking_date": row.get("booking_date") or row.get("posting_date"), "meeting_room": row.get("meeting_room"), "from_time": row.get("from_time"), "to_time": row.get("to_time"), "employee_name": row.get("employee_name"), "attendee_count": cint(row.get("attendee_count")), "status": row.get("status")})
        rows.sort(key=lambda item: (item["booking_date"] or "", item["meeting_room"] or "", item["from_time"] or ""))
        return _dataset(template, [("booking_date", "Ngày họp", "Date"), ("meeting_room", "Phòng họp", "Data"), ("from_time", "Từ giờ", "Data"), ("to_time", "Đến giờ", "Data"), ("employee_name", "Người đặt", "Data"), ("attendee_count", "Số người", "Int"), ("status", "Trạng thái", "Data")], rows, [_summary("Lượt đặt phòng", len(rows), "Int")])

    grouped = defaultdict(lambda: {"booking_count": 0, "total_hours": 0.0, "attendee_count": 0})
    for row in records:
        room = row.get("meeting_room") or "Chưa chọn phòng"
        grouped[room]["booking_count"] += 1
        grouped[room]["total_hours"] += _time_diff_hours(row.get("from_time"), row.get("to_time"))
        grouped[room]["attendee_count"] += cint(row.get("attendee_count"))
    rows = [{"meeting_room": room, "booking_count": item["booking_count"], "total_hours": item["total_hours"], "average_attendee": (item["attendee_count"] / item["booking_count"]) if item["booking_count"] else 0} for room, item in grouped.items()]
    rows.sort(key=lambda item: -item["total_hours"])
    if report_id == "meeting-room-utilization":
        return _dataset(template, [("meeting_room", "Phòng họp", "Data"), ("booking_count", "Số lượt đặt", "Int"), ("total_hours", "Tổng giờ sử dụng", "Float"), ("average_attendee", "Số người TB", "Float")], rows, [_summary("Phòng được dùng", len(rows), "Int"), _summary("Tổng giờ sử dụng", sum(item["total_hours"] for item in rows), "Float")])
    return _dataset(template, [("meeting_room", "Phòng họp", "Data"), ("booking_count", "Số lượt đặt", "Int"), ("total_hours", "Tổng giờ", "Float"), ("average_attendee", "Số người TB", "Float")], rows[:10], [_summary("Top phòng họp", min(len(rows), 10), "Int"), _summary("Tổng giờ sử dụng", sum(item["total_hours"] for item in rows), "Float")])


def _build_document_report(report_id, filters, template):
    employee_map = _get_employee_map()
    records = _apply_common_filters(_get_records("hrm-document-archive"), filters, employee_map)
    if report_id == "document-stock-by-type":
        grouped = defaultdict(lambda: {"document_count": 0, "storage_locations": set()})
        for row in records:
            doc_type = row.get("document_type") or "Chưa phân loại"
            grouped[doc_type]["document_count"] += 1
            if row.get("storage_location"):
                grouped[doc_type]["storage_locations"].add(row.get("storage_location"))
        rows = [{"document_type": key, "document_count": item["document_count"], "storage_location": ", ".join(sorted(item["storage_locations"])) or "Chưa cập nhật"} for key, item in grouped.items()]
        rows.sort(key=lambda item: -item["document_count"])
        return _dataset(template, [("document_type", "Loại hồ sơ", "Data"), ("document_count", "Số hồ sơ", "Int"), ("storage_location", "Vị trí lưu", "Data")], rows, [_summary("Loại hồ sơ", len(rows), "Int"), _summary("Tổng hồ sơ", sum(item["document_count"] for item in rows), "Int")])
    if report_id == "documents-expiring":
        base_date = getdate(_get_filter_month(filters))
        end_window = add_days(base_date, 60)
        rows = []
        for row in records:
            retention_until = _parse_date(row.get("retention_until"))
            if not retention_until or retention_until < base_date or retention_until > end_window:
                continue
            rows.append({"document_title": row.get("document_title") or row.get("title"), "document_type": row.get("document_type"), "employee_name": row.get("employee_name"), "retention_until": retention_until.isoformat(), "storage_location": row.get("storage_location"), "status": row.get("status")})
        rows.sort(key=lambda item: item["retention_until"])
        return _dataset(template, [("document_title", "Tên hồ sơ", "Data"), ("document_type", "Loại hồ sơ", "Data"), ("employee_name", "Nhân sự", "Data"), ("retention_until", "Lưu đến", "Date"), ("storage_location", "Vị trí lưu", "Data"), ("status", "Trạng thái", "Data")], rows, [_summary("Hồ sơ sắp hết hạn", len(rows), "Int")])

    required_docs = {"CCCD", "Hợp đồng lao động", "Sơ yếu lý lịch"}
    doc_map = defaultdict(set)
    for row in records:
        if row.get("employee_code") and row.get("document_type"):
            doc_map[row.get("employee_code")].add(str(row.get("document_type")))
    employees = _apply_common_filters(_get_records("hrm-employee-profile"), filters)
    rows = []
    for employee in employees:
        missing = sorted(required_docs - doc_map.get(employee.get("employee_code"), set()))
        if not missing:
            continue
        rows.append({"employee_name": employee.get("employee_name") or employee.get("full_name"), "department": employee.get("department"), "missing_documents": ", ".join(missing), "missing_count": len(missing), "status": employee.get("status")})
    rows.sort(key=lambda item: (-item["missing_count"], item["employee_name"] or ""))
    return _dataset(template, [("employee_name", "Nhân sự", "Data"), ("department", "Phòng ban", "Data"), ("missing_documents", "Hồ sơ còn thiếu", "Data"), ("missing_count", "Số hồ sơ thiếu", "Int"), ("status", "Trạng thái", "Data")], rows, [_summary("Nhân sự thiếu hồ sơ bắt buộc", len(rows), "Int")])


def _build_offboarding_report(report_id, filters, template):
    records = _apply_common_filters(_get_records("hrm-offboarding"), filters)
    if report_id == "offboarding-open-cases":
        rows = [
            {"employee_name": row.get("employee_name"), "department": row.get("department"), "resignation_date": row.get("resignation_date"), "last_working_date": row.get("last_working_date"), "handover_to": row.get("handover_to"), "status": row.get("status")}
            for row in records
            if row.get("status") != "Completed"
        ]
        rows.sort(key=lambda item: (item["last_working_date"] or "", item["employee_name"] or ""))
        return _dataset(template, [("employee_name", "Nhân sự", "Data"), ("department", "Phòng ban", "Data"), ("resignation_date", "Ngày nộp đơn", "Date"), ("last_working_date", "Ngày làm cuối", "Date"), ("handover_to", "Bàn giao cho", "Data"), ("status", "Trạng thái", "Data")], rows, [_summary("Hồ sơ đang mở", len(rows), "Int")])
    if report_id == "offboarding-monthly-trend":
        grouped = defaultdict(lambda: {"case_count": 0, "settlement_total": 0.0, "completed_count": 0})
        for row in records:
            month_key = str(row.get("resignation_date") or row.get("posting_date") or "")[:7] or "Chưa cập nhật"
            grouped[month_key]["case_count"] += 1
            grouped[month_key]["settlement_total"] += flt(row.get("final_settlement"))
            if row.get("status") == "Completed":
                grouped[month_key]["completed_count"] += 1
        rows = [{"month": key, "case_count": item["case_count"], "settlement_total": item["settlement_total"], "completion_rate": round((item["completed_count"] / item["case_count"]) * 100, 1) if item["case_count"] else 0} for key, item in grouped.items()]
        rows.sort(key=lambda item: item["month"], reverse=True)
        return _dataset(template, [("month", "Tháng", "Data"), ("case_count", "Số hồ sơ", "Int"), ("settlement_total", "Quyết toán", "Currency"), ("completion_rate", "Hoàn tất (%)", "Percent")], rows, [_summary("Số tháng có dữ liệu", len(rows), "Int"), _summary("Tổng quyết toán", sum(item["settlement_total"] for item in rows), "Currency")])

    rows = []
    for row in records:
        missing_steps = []
        if not row.get("handover_to"):
            missing_steps.append("Chưa có người nhận bàn giao")
        if not row.get("exit_interview"):
            missing_steps.append("Chưa có biên bản phỏng vấn")
        if not flt(row.get("final_settlement")):
            missing_steps.append("Chưa cập nhật quyết toán")
        if not missing_steps:
            continue
        rows.append({"employee_name": row.get("employee_name"), "department": row.get("department"), "last_working_date": row.get("last_working_date"), "missing_steps": "; ".join(missing_steps), "status": row.get("status")})
    rows.sort(key=lambda item: (item["last_working_date"] or "", item["employee_name"] or ""))
    return _dataset(template, [("employee_name", "Nhân sự", "Data"), ("department", "Phòng ban", "Data"), ("last_working_date", "Ngày làm cuối", "Date"), ("missing_steps", "Checklist còn thiếu", "Data"), ("status", "Trạng thái", "Data")], rows, [_summary("Hồ sơ thiếu checklist", len(rows), "Int")])


def _get_records(page_key):
    rows = frappe.db.sql(
        f"""
        select name, page_key, title, status, subject, employee_code, employee_name, company,
               posting_date, start_date, end_date, amount, file_url, payload_json, updated_at
          from `{HRM_RECORD_TABLE}`
         where page_key=%s
         order by updated_at desc
         limit 5000
        """,
        (page_key,),
        as_dict=True,
    )
    return [deserialize_record(frappe._dict(row)) for row in rows]


def _get_employee_map():
    output = {}
    for row in _get_records("hrm-employee-profile"):
        if row.get("employee_code"):
            output[row.get("employee_code")] = row
        if row.get("employee_name"):
            output[row.get("employee_name")] = row
        if row.get("full_name"):
            output[row.get("full_name")] = row

    employee_rows = frappe.get_all("Employee", fields=["name", "employee_name", "department", "company", "designation", "date_of_joining"], limit=5000)
    for row in employee_rows:
        payload = {
            "employee_code": row.name,
            "employee_name": row.employee_name,
            "department": row.department,
            "company": row.company,
            "designation": row.designation,
            "join_date": str(row.date_of_joining or ""),
        }
        output[row.name] = payload
        if row.employee_name:
            output[row.employee_name] = payload
    return output


def _apply_common_filters(records, filters=None, employee_map=None):
    filters = filters or {}
    department = (filters.get("department") or "").strip().lower()
    company = (filters.get("company") or "").strip().lower()
    employee_keyword = (filters.get("employee_keyword") or "").strip().lower()
    output = []
    for row in records:
        profile = (employee_map or {}).get(row.get("employee_code"), {})
        row_department = str(row.get("department") or profile.get("department") or "").lower()
        row_company = str(row.get("company") or profile.get("company") or "").lower()
        row_employee = str(row.get("employee_name") or "").lower()
        row_code = str(row.get("employee_code") or "").lower()
        if department and department not in row_department:
            continue
        if company and company not in row_company:
            continue
        if employee_keyword and employee_keyword not in row_employee and employee_keyword not in row_code:
            continue
        output.append(row)
    return output


def _filter_by_month(records, filters, date_fields):
    target_month = str((filters or {}).get("month") or "")[:7]
    if not target_month:
        return records
    output = []
    for row in records:
        for fieldname in date_fields:
            month_value = str(row.get(fieldname) or "")[:7]
            if month_value == target_month:
                output.append(row)
                break
    return output


def _dataset(template, columns, rows, summary):
    return {
        "title": template["title"],
        "description": template["description"],
        "columns": [{"fieldname": fieldname, "label": label, "type": fieldtype} for fieldname, label, fieldtype in columns],
        "rows": rows,
        "summary": summary,
        "row_count": len(rows),
        "empty_message": "Không có dữ liệu phù hợp với bộ lọc hiện tại." if not rows else "",
    }


def _summary(label, value, value_type="Data"):
    return {"label": label, "value": value, "type": value_type}


def _get_filter_month(filters):
    value = (filters or {}).get("month")
    return value or frappe.utils.today()


def _parse_date(value):
    if not value:
        return None
    try:
        return getdate(value)
    except Exception:
        return None


def _working_days_in_month(year, month):
    current = getdate(f"{year}-{month:02d}-01")
    end = get_last_day(current)
    total = 0
    while current <= end:
        if current.weekday() < 5:
            total += 1
        current += timedelta(days=1)
    return total


def _average(values):
    cleaned = [flt(value) for value in values if value not in (None, "")]
    return round(sum(cleaned) / len(cleaned), 1) if cleaned else 0


def _ratio_percent(part, total):
    return round((flt(part) / flt(total)) * 100, 1) if total else 0


def _year_delta(from_date, to_date):
    start = _parse_date(from_date)
    end = _parse_date(to_date)
    if not start or not end:
        return 0
    return round((end - start).days / 365, 1)


def _score_rank(score):
    score = flt(score)
    if score >= 90:
        return "Xuất sắc"
    if score >= 80:
        return "Tốt"
    if score >= 70:
        return "Đạt"
    return "Cần cải thiện"


def _time_diff_hours(from_time, to_time):
    if not from_time or not to_time:
        return 0
    try:
        from_hour, from_minute = [cint(part) for part in str(from_time).split(":")[:2]]
        to_hour, to_minute = [cint(part) for part in str(to_time).split(":")[:2]]
        return round(((to_hour * 60 + to_minute) - (from_hour * 60 + from_minute)) / 60, 2)
    except Exception:
        return 0


def _render_report_pdf_html(dataset):
    summary_html = "".join(
        f"""
        <div style="display:inline-block;margin:0 12px 12px 0;padding:10px 14px;border:1px solid #e5e7eb;border-radius:10px;min-width:150px;">
            <div style="font-size:11px;color:#6b7280;">{frappe.utils.escape_html(item['label'])}</div>
            <div style="font-size:16px;font-weight:700;color:#111827;">{frappe.utils.escape_html(_format_report_value(item.get('type'), item.get('value')))}</div>
        </div>
        """
        for item in dataset.get("summary", [])
    )
    header_html = "".join(f"<th style='padding:8px;border:1px solid #d1d5db;background:#f8fafc;text-align:left;'>{frappe.utils.escape_html(col['label'])}</th>" for col in dataset.get("columns", []))
    body_html = "".join(
        "<tr>"
        + "".join(
            f"<td style='padding:8px;border:1px solid #e5e7eb;'>{frappe.utils.escape_html(_format_report_value(column.get('type'), row.get(column['fieldname'])))}</td>"
            for column in dataset.get("columns", [])
        )
        + "</tr>"
        for row in dataset.get("rows", [])
    )
    if not body_html:
        body_html = f"<tr><td colspan='{len(dataset.get('columns', [])) or 1}' style='padding:14px;border:1px solid #e5e7eb;color:#6b7280;'>{frappe.utils.escape_html(dataset.get('empty_message') or 'Không có dữ liệu')}</td></tr>"
    return f"""
    <html>
      <body style="font-family:Arial, sans-serif;color:#111827;">
        <h2 style="margin-bottom:6px;">{frappe.utils.escape_html(dataset.get('title') or 'HRM Report')}</h2>
        <div style="color:#4b5563;margin-bottom:18px;">{frappe.utils.escape_html(dataset.get('description') or '')}</div>
        <div style="margin-bottom:18px;">{summary_html}</div>
        <table style="width:100%;border-collapse:collapse;font-size:12px;">
          <thead><tr>{header_html}</tr></thead>
          <tbody>{body_html}</tbody>
        </table>
      </body>
    </html>
    """


def _format_report_value(value_type, value):
    if value in (None, ""):
        return ""
    if value_type == "Currency":
        return f"{flt(value):,.0f}"
    if value_type in {"Float", "Percent"}:
        return f"{flt(value):,.1f}"
    if value_type == "Int":
        return f"{cint(value):,}"
    if value_type == "Date":
        try:
            return formatdate(value)
        except Exception:
            return str(value)
    return str(value)

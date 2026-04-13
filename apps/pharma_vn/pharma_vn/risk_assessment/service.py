from __future__ import annotations

import json
import os
import unicodedata
from datetime import date, datetime, timedelta, timezone

import frappe
import requests
from frappe import _
from frappe.utils import cint, cstr, flt, now_datetime

from pharma_vn.customer_naming import CUSTOMER_NAMING_SERIES


DEFAULT_RISK_ENGINE_URL = "http://localhost:5000/api/risk/check"
DEFAULT_XINVOICE_TAX_API_URL = "https://api.xinvoice.vn/gdt-api/tax-payer/{tax_code}"
DEFAULT_CACHE_TTL_MINUTES = 24 * 60
DEFAULT_HISTORY_LIMIT = 5
RISK_LEVELS = {"SAFE", "WARNING", "HIGH"}
CREDIT_STATUS_BY_RISK_LEVEL = {
    "SAFE": "Approved",
    "WARNING": "Pending",
    "HIGH": "Blocked",
}
LEVEL_ALIASES = {
    "LOW": "SAFE",
    "MEDIUM": "WARNING",
    "WARN": "WARNING",
    "DANGER": "HIGH",
}
CITY_ALIASES = {
    "TP HCM": "Ho Chi Minh City",
    "TPHCM": "Ho Chi Minh City",
    "TP HO CHI MINH": "Ho Chi Minh City",
    "THANH PHO HO CHI MINH": "Ho Chi Minh City",
    "HO CHI MINH": "Ho Chi Minh City",
    "HO CHI MINH CITY": "Ho Chi Minh City",
    "TP HA NOI": "Hanoi",
    "THANH PHO HA NOI": "Hanoi",
    "HA NOI": "Hanoi",
    "HANOI": "Hanoi",
    "TP DA NANG": "Da Nang",
    "THANH PHO DA NANG": "Da Nang",
    "DA NANG": "Da Nang",
}
COUNTRY_TOKENS = {"VIET NAM", "VIETNAM", "VN"}
DEFAULT_NO_REASON_MESSAGE = "Risk engine did not provide detailed reasons."
INDUSTRY_RISK_RULES = (
    {
        "score": 16,
        "keywords": (
            "BAT DONG SAN",
            "REAL ESTATE",
            "PROPERTY DEVELOPMENT",
            "PROPERTY INVESTMENT",
        ),
        "reason": "Registered business line indicates elevated risk: {0}.",
    },
    {
        "score": 16,
        "keywords": (
            "TAI CHINH",
            "NGAN HANG",
            "TIN DUNG",
            "CHO VAY",
            "CAM DO",
            "CHUNG KHOAN",
            "DAU TU",
            "FINANCE",
            "BANK",
            "BANKING",
            "LENDING",
            "PAWN",
            "SECURITIES",
            "INVESTMENT",
        ),
        "reason": "Registered business line indicates elevated risk: {0}.",
    },
    {
        "score": 18,
        "keywords": (
            "TIEN AO",
            "CRYPTO",
            "VIRTUAL ASSET",
            "CASINO",
            "CA CUOC",
            "BETTING",
            "GAMBLING",
            "TRO CHOI CO THUONG",
        ),
        "reason": "Registered business line indicates elevated risk: {0}.",
    },
    {
        "score": 8,
        "keywords": (
            "XAY DUNG",
            "CONSTRUCTION",
            "LOGISTICS",
            "VAN TAI",
            "TRANSPORT",
            "IMPORT EXPORT",
            "XUAT NHAP KHAU",
            "PETROLEUM",
            "FUEL",
        ),
        "reason": "Registered business line should be reviewed closely: {0}.",
    },
)
STANDARD_CUSTOMER_FIELDS = {
    "customer_name",
    "customer_primary_address",
    "customer_primary_contact",
    "tax_id",
}


def check_customer_risk(customer=None, tax_code=None, force_refresh=False):
    customer = _resolve_customer_name(customer=customer, tax_code=tax_code)
    tax_code = normalize_tax_code(tax_code or _get_customer_tax_code(customer))
    if not customer:
        frappe.throw(_("A valid Customer is required before checking risk."))
    if not tax_code:
        frappe.throw(_("Tax ID / tax_code is required before checking customer risk."))

    cached_profile = get_latest_customer_risk_profile(customer=customer)
    if cached_profile and not cint(force_refresh) and should_use_cached_profile(cached_profile, tax_code=tax_code):
        return build_profile_response(cached_profile, from_cache=True)

    business_profile = None
    warnings = []
    if has_business_profile_lookup():
        business_profile, warning_message = fetch_tax_business_profile(tax_code)
        if warning_message:
            warnings.append(warning_message)
    customer_updates = sync_customer_business_profile(customer, business_profile, tax_code)

    try:
        engine_response = call_risk_engine(
            customer=customer,
            tax_code=tax_code,
            business_profile=business_profile,
        )
    except Exception as exc:
        warning_message = cstr(exc).strip()
        if warning_message:
            warnings.append(warning_message)
        if cached_profile or business_profile:
            return build_engine_unavailable_response(
                customer=customer,
                tax_code=tax_code,
                business_profile=business_profile,
                warnings=warnings,
                cached_profile=cached_profile,
                customer_updates=customer_updates,
            )
        raise
    normalized = normalize_risk_payload(
        engine_response,
        customer=customer,
        tax_code=tax_code,
        business_profile=business_profile,
        warnings=warnings,
    )
    normalized["customer_updates"] = customer_updates
    profile = save_customer_risk_profile(customer=customer, normalized_result=normalized)
    return build_profile_response(profile, from_cache=False)


def get_customer_risk_snapshot(customer):
    customer = cstr(customer).strip()
    if not customer:
        frappe.throw(_("Customer is required"))

    latest = get_latest_customer_risk_profile(customer=customer)
    tax_code = normalize_tax_code(_get_customer_tax_code(customer))
    if latest and should_use_cached_profile(latest, tax_code=tax_code):
        return build_profile_response(latest, from_cache=True)
    if latest and tax_code:
        try:
            return check_customer_risk(customer=customer, tax_code=tax_code, force_refresh=True)
        except Exception:
            return build_profile_response(latest, from_cache=True)

    return {
        "status": "empty",
        "customer": customer,
        "tax_code": tax_code,
        "risk_score": None,
        "risk_level": "",
        "last_check_date": None,
        "reasons": [],
        "reasons_text": "",
        "history": [],
        "message": _("No customer risk assessment has been run yet."),
    }


def get_latest_customer_risk_profile(customer):
    customer = cstr(customer).strip()
    if not customer:
        return None

    rows = frappe.get_all(
        "Customer Risk Profile",
        filters={"customer": customer},
        fields=[
            "name",
            "customer",
            "tax_code",
            "risk_score",
            "risk_level",
            "last_check_date",
            "reasons",
            "raw_response",
            "modified",
        ],
        order_by="last_check_date desc, modified desc",
        limit_page_length=1,
    )
    if not rows:
        return None
    return rows[0]


def list_customer_risk_history(customer, limit=DEFAULT_HISTORY_LIMIT):
    customer = cstr(customer).strip()
    if not customer:
        return []

    rows = frappe.get_all(
        "Customer Risk Profile",
        filters={"customer": customer},
        fields=["name", "risk_score", "risk_level", "last_check_date", "reasons"],
        order_by="last_check_date desc, modified desc",
        limit_page_length=cint(limit or DEFAULT_HISTORY_LIMIT),
    )
    return [serialize_history_row(row) for row in rows]


def normalize_tax_code(value):
    return cstr(value).strip().replace(" ", "").upper()


def normalize_risk_payload(raw_payload, customer=None, tax_code=None, business_profile=None, warnings=None):
    payload = raw_payload or {}
    data = payload.get("data") if isinstance(payload, dict) and isinstance(payload.get("data"), dict) else payload
    score = coerce_risk_score(first_value(data, "risk_score", "riskScore", "score", "total_score"))
    checked_at = coerce_datetime(first_value(data, "last_check_date", "checked_at", "checkedAt", "timestamp")) or now_datetime()
    business_profile = normalize_business_profile(business_profile or first_value(data, "business_profile", "businessProfile"))
    profile_risk_signals = assess_business_profile_risk(business_profile)
    score = min(100, max(0, score + cint(profile_risk_signals.get("score_adjustment") or 0)))
    level = infer_risk_level(score, first_value(data, "risk_level", "riskLevel", "level"))
    reasons = merge_risk_reasons(extract_reasons(data), profile_risk_signals.get("reasons"))
    warning_items = [cstr(item).strip() for item in (warnings or []) if cstr(item).strip()]

    return {
        "status": "ready",
        "customer": customer,
        "tax_code": normalize_tax_code(tax_code),
        "risk_score": score,
        "risk_level": level,
        "last_check_date": checked_at,
        "reasons": reasons,
        "reasons_text": "\n".join(reasons),
        "business_profile": business_profile,
        "warnings": warning_items,
        "message": first_value(payload, "message", "detail") or _("Risk assessment completed"),
        "raw_response": {
            "risk_engine": raw_payload,
            "business_profile": business_profile,
            "profile_risk_signals": profile_risk_signals,
            "warnings": warning_items,
            "customer_updates": {},
        },
    }


def infer_risk_level(score, provided_level=None):
    normalized = LEVEL_ALIASES.get(cstr(provided_level).strip().upper(), cstr(provided_level).strip().upper())
    if normalized in RISK_LEVELS:
        return normalized

    score = cint(score or 0)
    if score >= 70:
        return "HIGH"
    if score >= 40:
        return "WARNING"
    return "SAFE"


def extract_reasons(payload):
    reasons = first_value(payload, "reasons", "reason_list", "reasonList", "factors", "signals")
    if isinstance(reasons, str):
        return [
            cstr(line).lstrip("-").strip()
            for line in reasons.splitlines()
            if cstr(line).lstrip("-").strip()
        ]

    if isinstance(reasons, (list, tuple)):
        items = []
        for row in reasons:
            if isinstance(row, dict):
                text = (
                    first_value(row, "message", "reason", "name", "title", "description")
                    or json.dumps(row, ensure_ascii=False, default=str)
                )
            else:
                text = cstr(row)
            text = cstr(text).strip()
            if text:
                items.append(text)
        if items:
            return items

    single_reason = first_value(payload, "reason", "message", "detail")
    if cstr(single_reason).strip():
        return [cstr(single_reason).strip()]

    return [_(DEFAULT_NO_REASON_MESSAGE)]


def merge_risk_reasons(engine_reasons, profile_reasons):
    engine_reasons = [cstr(reason).strip() for reason in (engine_reasons or []) if cstr(reason).strip()]
    profile_reasons = [cstr(reason).strip() for reason in (profile_reasons or []) if cstr(reason).strip()]
    if not profile_reasons:
        return engine_reasons or [_(DEFAULT_NO_REASON_MESSAGE)]
    if engine_reasons == [_(DEFAULT_NO_REASON_MESSAGE)]:
        return profile_reasons
    return merge_message_lists(engine_reasons, profile_reasons)


def call_risk_engine(customer, tax_code, business_profile=None):
    endpoint = _get_setting("risk_engine_url", "PHARMA_VN_RISK_ENGINE_URL", DEFAULT_RISK_ENGINE_URL)
    headers = {"Content-Type": "application/json"}
    api_key = _get_setting("risk_engine_api_key", "PHARMA_VN_RISK_ENGINE_API_KEY")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "customer": customer,
        "tax_code": tax_code,
    }
    if business_profile:
        payload["business_profile"] = business_profile

    timeout = flt(_get_setting("risk_engine_timeout", "PHARMA_VN_RISK_ENGINE_TIMEOUT", 20)) or 20
    try:
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
    except requests.HTTPError as exc:
        frappe.throw(_("Risk engine request failed: {0}").format(extract_request_error(exc.response)))
    except requests.RequestException as exc:
        frappe.throw(_("Could not reach the risk engine at {0}: {1}").format(endpoint, exc))

    if not response.content:
        return {}

    try:
        return response.json()
    except ValueError:
        return {"message": response.text or _("Risk engine returned an empty response")}


def has_business_profile_lookup():
    return bool(get_business_profile_api_config().get("endpoint"))


def get_business_profile_api_config():
    endpoint = _get_setting("tax_business_api_url", "PHARMA_VN_TAX_BUSINESS_API_URL")
    source = _get_setting("tax_business_api_source", "PHARMA_VN_TAX_BUSINESS_API_SOURCE", "XInvoice Tax API")
    method = _get_setting("tax_business_api_method", "PHARMA_VN_TAX_BUSINESS_API_METHOD", "GET")
    api_key = _get_setting("tax_business_api_key", "PHARMA_VN_TAX_BUSINESS_API_KEY")
    client_id = _get_setting("tax_business_api_client_id", "PHARMA_VN_TAX_BUSINESS_API_CLIENT_ID")
    timeout = _get_setting("tax_business_api_timeout", "PHARMA_VN_TAX_BUSINESS_API_TIMEOUT", 10)

    if not endpoint:
        endpoint = _get_setting("xinvoice_tax_api_url", "PHARMA_VN_XINVOICE_TAX_API_URL", DEFAULT_XINVOICE_TAX_API_URL)
        method = _get_setting("xinvoice_tax_api_method", "PHARMA_VN_XINVOICE_TAX_API_METHOD", method)
        api_key = _get_setting("xinvoice_tax_api_key", "PHARMA_VN_XINVOICE_TAX_API_KEY", api_key)
        client_id = _get_setting("xinvoice_tax_api_client_id", "PHARMA_VN_XINVOICE_TAX_API_CLIENT_ID", client_id)
        timeout = _get_setting("xinvoice_tax_api_timeout", "PHARMA_VN_XINVOICE_TAX_API_TIMEOUT", timeout)
        source = _get_setting("xinvoice_tax_api_source", "PHARMA_VN_XINVOICE_TAX_API_SOURCE", "XInvoice Tax API")

    if not endpoint:
        endpoint = _get_setting("vietqr_business_api_url", "PHARMA_VN_VIETQR_BUSINESS_API_URL")
        method = _get_setting("vietqr_business_api_method", "PHARMA_VN_VIETQR_BUSINESS_API_METHOD", method)
        api_key = _get_setting("vietqr_business_api_key", "PHARMA_VN_VIETQR_BUSINESS_API_KEY", api_key)
        timeout = _get_setting("vietqr_business_api_timeout", "PHARMA_VN_VIETQR_BUSINESS_API_TIMEOUT", timeout)
        source = _get_setting("vietqr_business_api_source", "PHARMA_VN_VIETQR_BUSINESS_API_SOURCE", "VietQR Business API")

    return {
        "endpoint": endpoint,
        "method": cstr(method).strip().upper() or "GET",
        "api_key": api_key,
        "client_id": client_id,
        "timeout": flt(timeout) or 10,
        "source": source,
    }


def fetch_tax_business_profile(tax_code):
    config = get_business_profile_api_config()
    endpoint = config["endpoint"]
    if not endpoint:
        return None, None

    method = config["method"]
    request_url = endpoint.format(tax_code=tax_code) if "{tax_code}" in endpoint else endpoint
    headers = {"Accept": "application/json"}
    api_key = config["api_key"]
    client_id = config.get("client_id")
    if api_key:
        headers["x-api-key"] = api_key
        headers["api-key"] = api_key
    if client_id:
        headers["client-id"] = client_id
    if api_key and not client_id:
        headers["Authorization"] = f"Bearer {api_key}"

    request_kwargs = {
        "headers": headers,
        "timeout": config["timeout"],
    }
    if method == "GET":
        if "{tax_code}" not in endpoint:
            request_kwargs["params"] = {"tax_code": tax_code}
    else:
        request_kwargs["json"] = {"tax_code": tax_code}

    try:
        response = requests.request(method, request_url, **request_kwargs)
        response.raise_for_status()
    except requests.RequestException as exc:
        return None, _("{0} lookup failed: {1}").format(config["source"], exc)

    try:
        payload = response.json()
    except ValueError:
        return None, _("{0} returned invalid JSON.").format(config["source"])

    return normalize_business_profile(payload, source=config["source"]), None


def quick_create_customer_from_tax_id(tax_code, customer_type="Company"):
    tax_code = normalize_tax_code(tax_code)
    if not tax_code:
        frappe.throw(_("Tax ID / tax_code is required before creating a customer."))

    existing_customer = _resolve_customer_name(tax_code=tax_code)
    if existing_customer:
        return {
            "status": "existing",
            "customer": existing_customer,
            "customer_name": cstr(frappe.db.get_value("Customer", existing_customer, "customer_name")).strip() or existing_customer,
            "tax_code": tax_code,
        }

    business_profile, warning_message = fetch_tax_business_profile(tax_code)
    if warning_message:
        frappe.throw(warning_message)
    if not business_profile:
        frappe.throw(_("Could not load business information for tax ID {0}.").format(tax_code))

    resolved_customer_group = _get_default_customer_group()
    resolved_territory = _get_default_territory()
    if not resolved_customer_group:
        frappe.throw(_("Could not find a default Customer Group for quick customer creation."))
    if not resolved_territory:
        frappe.throw(_("Could not find a default Territory for quick customer creation."))

    customer_name = (
        cstr(business_profile.get("company_name") or business_profile.get("short_name")).strip()
        or _("Customer MST {0}").format(tax_code)
    )
    customer_doc = frappe.get_doc(
        {
            "doctype": "Customer",
            "customer_name": customer_name,
            "customer_type": normalize_customer_type(customer_type),
            "customer_group": resolved_customer_group,
            "territory": resolved_territory,
            "tax_id": tax_code,
            **({"tax_code": tax_code} if _customer_has_field("tax_code") else {}),
            **({"naming_series": CUSTOMER_NAMING_SERIES} if _customer_has_field("naming_series") else {}),
        }
    )
    customer_doc.insert(ignore_permissions=True)

    customer_updates = sync_customer_business_profile(customer_doc.name, business_profile, tax_code=tax_code)
    return {
        "status": "created",
        "customer": customer_doc.name,
        "customer_name": customer_updates.get("customer_name") or customer_name,
        "tax_code": tax_code,
        "business_profile": business_profile,
        "customer_updates": customer_updates,
        "customer_group": resolved_customer_group,
        "territory": resolved_territory,
    }


def normalize_business_profile(payload, source=None):
    if not payload:
        return None

    source = cstr(source or first_value(payload, "source", "provider")).strip() or "Tax Business API"
    candidate = payload
    if isinstance(payload, dict):
        for key in ("data", "result", "company", "business", "enterprise"):
            if isinstance(payload.get(key), dict):
                candidate = payload.get(key)
                break
    if not isinstance(candidate, dict):
        return {"source": source, "raw": cstr(candidate)}

    profile = {
        "company_name": first_value(candidate, "company_name", "companyName", "legal_name", "legalName", "full_name", "fullName", "name", "tenDoanhNghiep", "ten"),
        "short_name": first_value(candidate, "short_name", "shortName", "brand_name", "brandName", "tenVietTat"),
        "tax_code": normalize_tax_code(first_value(candidate, "tax_code", "taxCode", "taxID", "mst")),
        "address": first_value(candidate, "address", "registered_address", "registeredAddress", "diaChiTruSo", "diaChi"),
        "address_line2": first_value(candidate, "address_line2", "addressLine2", "ward", "phuongXa"),
        "city": first_value(candidate, "city", "province", "provinceName", "district", "quanHuyen", "thanhPho"),
        "state": first_value(candidate, "state", "region", "stateName", "tinhThanh"),
        "country": first_value(candidate, "country", "countryName", "quocGia"),
        "status": first_value(candidate, "status", "company_status", "companyStatus", "tinhTrangHoatDong", "trangThai"),
        "organization_type": first_value(candidate, "orgType", "organization_type", "organizationType", "loaiHinh"),
        "tax_department": first_value(candidate, "taxDepartment", "tax_department", "taxDepartmentName", "coQuanThue"),
        "representative": first_value(candidate, "legal_representative", "legalRepresentative", "owner", "nguoiDaiDien", "legal_person"),
        "established_date": format_date_value(
            first_value(
                candidate,
                "established_date",
                "establishedDate",
                "incorporation_date",
                "incorporationDate",
                "registration_date",
                "registrationDate",
                "founded_date",
                "foundedDate",
                "issueDate",
                "ngayThanhLap",
                "ngayDangKyLanDau",
                "ngayCap",
            )
        ),
        "business_lines": normalize_business_lines(
            first_value(
                candidate,
                "business_lines",
                "businessLines",
                "industry_list",
                "industryList",
                "industries",
                "industry",
                "sector",
                "main_business",
                "mainBusiness",
                "business_line",
                "businessLine",
                "nganhNgheKinhDoanh",
                "nganhNghe",
            )
        ),
        "email": first_value(candidate, "email", "emailAddress", "contactEmail"),
        "phone": first_value(candidate, "phone", "phoneNumber", "mobile", "contactPhone"),
        "website": first_value(candidate, "website", "webSite", "homepage"),
        "updated_at": first_value(candidate, "updatedAt", "updated_at", "lastUpdatedAt"),
        "source": source,
    }
    cleaned = {key: value for key, value in profile.items() if has_value(value)}
    return cleaned or None


def normalize_customer_type(value):
    normalized = cstr(value).strip().title()
    return normalized if normalized in {"Company", "Individual"} else "Company"


def assess_business_profile_risk(business_profile):
    if not isinstance(business_profile, dict):
        return {"score_adjustment": 0, "reasons": []}

    score_adjustment = 0
    reasons = []
    established_date = coerce_date_value(business_profile.get("established_date"))
    if established_date:
        age_days = max((now_datetime().date() - established_date).days, 0)
        if age_days < 365:
            score_adjustment += 18
            reasons.append(_("Business was established less than 12 months ago."))
        elif age_days < 365 * 3:
            score_adjustment += 8
            reasons.append(_("Business has a limited operating history of under 3 years."))

    matched_lines = set()
    for line in normalize_business_lines(business_profile.get("business_lines")):
        normalized_line = normalize_match_text(line)
        for rule in INDUSTRY_RISK_RULES:
            if any(keyword in normalized_line for keyword in rule["keywords"]):
                if line not in matched_lines:
                    matched_lines.add(line)
                    score_adjustment += cint(rule["score"])
                    reasons.append(_(rule["reason"]).format(line))
                break

    return {
        "score_adjustment": min(score_adjustment, 35),
        "reasons": reasons,
    }


def normalize_business_lines(value):
    if not value:
        return []

    if isinstance(value, str):
        raw_value = cstr(value).strip()
        if not raw_value:
            return []
        if raw_value.startswith("[") and raw_value.endswith("]"):
            try:
                parsed = json.loads(raw_value)
            except ValueError:
                parsed = None
            if parsed is not None:
                return normalize_business_lines(parsed)

        separators = ("\n", ";", "|")
        items = [raw_value]
        for separator in separators:
            if separator in raw_value:
                items = [part.strip(" -\t") for part in raw_value.split(separator)]
                break
        return [item for item in items if item]

    if isinstance(value, dict):
        text = first_value(value, "name", "title", "description", "industry", "business_line", "businessLine")
        return [cstr(text).strip()] if cstr(text).strip() else []

    if isinstance(value, (list, tuple, set)):
        items = []
        seen = set()
        for row in value:
            for item in normalize_business_lines(row):
                normalized_item = cstr(item).strip()
                if normalized_item and normalized_item not in seen:
                    seen.add(normalized_item)
                    items.append(normalized_item)
        return items

    text = cstr(value).strip()
    return [text] if text else []


def sync_customer_business_profile(customer, business_profile, tax_code=None):
    customer = cstr(customer).strip()
    if not customer or not isinstance(business_profile, dict):
        return {}

    updates = {}
    normalized_tax_code = normalize_tax_code(tax_code or business_profile.get("tax_code"))
    if normalized_tax_code:
        _sync_customer_field(customer, "tax_id", normalized_tax_code, updates)
        if _customer_has_field("tax_code"):
            _sync_customer_field(customer, "tax_code", normalized_tax_code, updates)

    company_name = cstr(business_profile.get("company_name") or business_profile.get("short_name")).strip()
    if company_name:
        _sync_customer_field(customer, "customer_name", company_name, updates)

    address_name = sync_customer_registered_address(
        customer,
        business_profile,
        address_title=company_name or customer,
    )
    if address_name:
        updates["customer_primary_address"] = address_name

    return updates


def sync_customer_registered_address(customer, business_profile, address_title=None):
    customer = cstr(customer).strip()
    address_line1 = cstr((business_profile or {}).get("address")).strip()
    if not customer or not address_line1 or not _customer_has_field("customer_primary_address"):
        return None

    address_title = cstr(address_title or business_profile.get("company_name") or customer).strip() or customer
    address_name = cstr(frappe.db.get_value("Customer", customer, "customer_primary_address")).strip()
    address_fields = _build_registered_address_fields(address_title, business_profile, address_line1, creating=not address_name)

    if not address_name:
        address_doc = frappe.get_doc(
            {
                "doctype": "Address",
                **address_fields,
                "links": [
                    {
                        "link_doctype": "Customer",
                        "link_name": customer,
                    }
                ],
            }
        ).insert(ignore_permissions=True)
        address_name = cstr(getattr(address_doc, "name", None)).strip()
        if address_name:
            _db_set_value("Customer", customer, "customer_primary_address", address_name, update_modified=False)
        return address_name or None

    for fieldname, value in address_fields.items():
        current_value = cstr(frappe.db.get_value("Address", address_name, fieldname)).strip()
        if current_value == cstr(value).strip():
            continue
        _db_set_value("Address", address_name, fieldname, value, update_modified=False)

    return address_name


def _build_registered_address_fields(address_title, business_profile, address_line1, creating=False):
    fields = {
        "address_title": address_title,
        "address_type": "Billing",
        "address_line1": address_line1,
    }

    address_line2 = cstr((business_profile or {}).get("address_line2")).strip()
    if address_line2:
        fields["address_line2"] = address_line2

    city = cstr((business_profile or {}).get("city")).strip()
    if not city:
        city = cstr((business_profile or {}).get("state")).strip()
    if not city:
        city = _infer_city_from_address(address_line1)
    if city:
        fields["city"] = city
    elif creating:
        fields["city"] = _("Unknown")

    state = cstr((business_profile or {}).get("state")).strip()
    if state:
        fields["state"] = state

    country = cstr((business_profile or {}).get("country")).strip()
    if country:
        fields["country"] = country
    elif creating:
        fields["country"] = "Vietnam"

    return fields


def _infer_city_from_address(address_line1):
    tokens = [
        cstr(token).strip(" ,.-")
        for token in cstr(address_line1).replace(";", ",").split(",")
        if cstr(token).strip(" ,.-")
    ]
    if not tokens:
        return ""

    for token in reversed(tokens):
        normalized = cstr(token).upper().replace(".", " ")
        normalized = " ".join(normalized.split())
        if normalized in COUNTRY_TOKENS:
            continue
        return CITY_ALIASES.get(normalized, token)

    return ""


def _sync_customer_field(customer, fieldname, value, updates):
    if not _customer_has_field(fieldname):
        return

    normalized_value = cstr(value).strip()
    if not normalized_value:
        return

    current_value = cstr(frappe.db.get_value("Customer", customer, fieldname)).strip()
    if current_value == normalized_value:
        return

    _db_set_value("Customer", customer, fieldname, normalized_value, update_modified=False)
    updates[fieldname] = normalized_value


def save_customer_risk_profile(customer, normalized_result):
    raw_response = {
        **(normalized_result["raw_response"] or {}),
        "customer_updates": normalized_result.get("customer_updates") or {},
    }
    doc = frappe.get_doc(
        {
            "doctype": "Customer Risk Profile",
            "customer": customer,
            "tax_code": normalized_result["tax_code"],
            "risk_score": normalized_result["risk_score"],
            "risk_level": normalized_result["risk_level"],
            "last_check_date": normalized_result["last_check_date"],
            "reasons": normalized_result["reasons_text"],
            "raw_response": json.dumps(
                raw_response,
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
        }
    )
    doc.insert(ignore_permissions=True)
    sync_customer_credit_review_status(customer, normalized_result["risk_level"])
    return doc


def build_profile_response(profile, from_cache=False):
    payload = parse_raw_response(getattr(profile, "raw_response", None))
    business_profile = normalize_business_profile(payload.get("business_profile"))
    reasons = parse_reasons(getattr(profile, "reasons", ""))
    warnings = merge_message_lists(payload.get("warnings"))
    customer_updates = payload.get("customer_updates") if isinstance(payload.get("customer_updates"), dict) else {}

    return {
        "status": "ready",
        "profile_name": getattr(profile, "name", None),
        "customer": getattr(profile, "customer", None),
        "tax_code": getattr(profile, "tax_code", None),
        "risk_score": cint(getattr(profile, "risk_score", 0) or 0),
        "risk_level": infer_risk_level(getattr(profile, "risk_score", 0), getattr(profile, "risk_level", None)),
        "last_check_date": getattr(profile, "last_check_date", None),
        "reasons": reasons,
        "reasons_text": "\n".join(reasons),
        "raw_response": payload.get("risk_engine") or payload,
        "business_profile": business_profile,
        "customer_updates": customer_updates,
        "warnings": warnings,
        "from_cache": 1 if from_cache else 0,
        "history": list_customer_risk_history(getattr(profile, "customer", None)),
        "message": _("Loaded cached customer risk profile") if from_cache else _("Risk assessment completed"),
    }


def serialize_history_row(row):
    reasons = parse_reasons(getattr(row, "reasons", None) if hasattr(row, "reasons") else row.get("reasons"))
    return {
        "name": getattr(row, "name", None) if hasattr(row, "name") else row.get("name"),
        "risk_score": cint(getattr(row, "risk_score", 0) if hasattr(row, "risk_score") else row.get("risk_score")),
        "risk_level": infer_risk_level(
            getattr(row, "risk_score", 0) if hasattr(row, "risk_score") else row.get("risk_score"),
            getattr(row, "risk_level", None) if hasattr(row, "risk_level") else row.get("risk_level"),
        ),
        "last_check_date": getattr(row, "last_check_date", None) if hasattr(row, "last_check_date") else row.get("last_check_date"),
        "reasons": reasons,
    }


def parse_raw_response(value):
    if not value:
        return {}
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return {"risk_engine": {"raw": cstr(value)}}
    return parsed if isinstance(parsed, dict) else {"risk_engine": parsed}


def parse_reasons(value):
    if not value:
        return []
    if isinstance(value, (list, tuple)):
        return [cstr(item).strip() for item in value if cstr(item).strip()]
    return [cstr(line).lstrip("-").strip() for line in cstr(value).splitlines() if cstr(line).lstrip("-").strip()]


def merge_message_lists(*groups):
    merged = []
    seen = set()
    for group in groups:
        if isinstance(group, (list, tuple, set)):
            items = group
        else:
            items = [group]
        for item in items:
            message = cstr(item).strip()
            if message and message not in seen:
                seen.add(message)
                merged.append(message)
    return merged


def build_engine_unavailable_response(
    customer,
    tax_code,
    business_profile=None,
    warnings=None,
    cached_profile=None,
    customer_updates=None,
):
    warning_items = merge_message_lists(warnings)
    customer_updates = customer_updates or {}

    if cached_profile:
        profile = enrich_profile_raw_response(
            cached_profile,
            business_profile=business_profile,
            warnings=warning_items,
            customer_updates=customer_updates,
        )
        response = build_profile_response(profile, from_cache=True)
        response["tax_code"] = tax_code or response.get("tax_code")
        response["business_profile"] = business_profile or response.get("business_profile")
        response["warnings"] = merge_message_lists(response.get("warnings"), warning_items)
        response["customer_updates"] = {
            **(response.get("customer_updates") or {}),
            **customer_updates,
        }
        response["message"] = _(
            "Business profile loaded, but the risk engine is currently unavailable. Showing the latest saved risk score."
        )
        return response

    return {
        "status": "ready",
        "profile_name": None,
        "customer": customer,
        "tax_code": tax_code,
        "risk_score": None,
        "risk_level": "",
        "last_check_date": None,
        "reasons": [],
        "reasons_text": "",
        "raw_response": {
            "risk_engine": {},
            "business_profile": business_profile,
            "warnings": warning_items,
            "customer_updates": customer_updates,
        },
        "business_profile": business_profile,
        "customer_updates": customer_updates,
        "warnings": warning_items,
        "from_cache": 0,
        "history": list_customer_risk_history(customer),
        "message": _("Business profile loaded, but the risk engine is currently unavailable."),
    }


def enrich_profile_raw_response(profile, business_profile=None, warnings=None, customer_updates=None):
    if not profile:
        return profile

    payload = parse_raw_response(_get_profile_value(profile, "raw_response"))
    if business_profile:
        payload["business_profile"] = business_profile
    if warnings:
        payload["warnings"] = merge_message_lists(payload.get("warnings"), warnings)
    if customer_updates:
        existing_updates = payload.get("customer_updates") if isinstance(payload.get("customer_updates"), dict) else {}
        payload["customer_updates"] = {**existing_updates, **customer_updates}

    raw_response = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    _set_profile_value(profile, "raw_response", raw_response)

    profile_name = _get_profile_value(profile, "name")
    if profile_name:
        try:
            frappe.db.set_value("Customer Risk Profile", profile_name, "raw_response", raw_response, update_modified=False)
        except TypeError:
            frappe.db.set_value("Customer Risk Profile", profile_name, "raw_response", raw_response)
        except Exception:
            pass

    return profile


def is_profile_fresh(profile):
    checked_at = coerce_datetime(getattr(profile, "last_check_date", None))
    if not checked_at:
        return False
    ttl_minutes = cint(_get_setting("risk_cache_ttl_minutes", "PHARMA_VN_RISK_CACHE_TTL_MINUTES", DEFAULT_CACHE_TTL_MINUTES))
    return now_datetime() - checked_at <= timedelta(minutes=ttl_minutes)


def should_use_cached_profile(profile, tax_code=None):
    if not profile or not is_profile_fresh(profile):
        return False

    requested_tax_code = normalize_tax_code(tax_code)
    profile_tax_code = normalize_tax_code(getattr(profile, "tax_code", None))
    if requested_tax_code and profile_tax_code and requested_tax_code != profile_tax_code:
        return False

    if not has_business_profile_lookup():
        return True

    payload = parse_raw_response(getattr(profile, "raw_response", None))
    business_profile = normalize_business_profile(payload.get("business_profile"))
    if not business_profile:
        return False

    configured_source = cstr(get_business_profile_api_config().get("source")).strip()
    profile_source = cstr(business_profile.get("source")).strip()
    if configured_source and profile_source and configured_source != profile_source:
        return False

    if requested_tax_code and normalize_tax_code(business_profile.get("tax_code")) not in {"", requested_tax_code}:
        return False

    if configured_source == "XInvoice Tax API":
        required_fields = ("company_name", "tax_code", "address", "status", "organization_type", "tax_department")
        if any(not cstr(business_profile.get(fieldname)).strip() for fieldname in required_fields):
            return False

    return True


def _get_profile_value(profile, fieldname):
    if isinstance(profile, dict):
        return profile.get(fieldname)
    return getattr(profile, fieldname, None)


def _set_profile_value(profile, fieldname, value):
    if isinstance(profile, dict):
        profile[fieldname] = value
        return
    try:
        setattr(profile, fieldname, value)
    except Exception:
        pass


def block_high_risk_sales_order(doc, method=None):
    if not cint(_get_setting("risk_block_sales_order_on_high", "PHARMA_VN_RISK_BLOCK_SALES_ORDER_ON_HIGH", 1)):
        return
    if not getattr(doc, "customer", None):
        return

    latest = get_latest_customer_risk_profile(doc.customer)
    if not latest:
        return

    if infer_risk_level(getattr(latest, "risk_score", 0), getattr(latest, "risk_level", None)) != "HIGH":
        return

    reasons = parse_reasons(getattr(latest, "reasons", ""))
    reason_summary = reasons[0] if reasons else _("No detailed reason provided")
    frappe.throw(
        _(
            "Customer {0} is currently HIGH risk based on the latest assessment dated {1}. "
            "Review Customer Risk Profile {2} before submitting this Sales Order. Reason: {3}"
        ).format(
            doc.customer,
            getattr(latest, "last_check_date", _("Unknown")),
            getattr(latest, "name", _("Unknown")),
            reason_summary,
        )
    )


def sync_customer_credit_review_status(customer, risk_level):
    customer = cstr(customer).strip()
    status = CREDIT_STATUS_BY_RISK_LEVEL.get(cstr(risk_level).strip().upper())
    if not customer or not status:
        return
    frappe.db.set_value("Customer", customer, "credit_review_status", status)


def coerce_risk_score(value):
    try:
        return cint(round(float(value or 0)))
    except (TypeError, ValueError):
        return 0


def coerce_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        dt_value = value
    else:
        try:
            dt_value = datetime.fromisoformat(cstr(value).replace("Z", "+00:00"))
        except ValueError:
            return None

    if dt_value.tzinfo is not None:
        dt_value = dt_value.astimezone(timezone.utc).replace(tzinfo=None)
    return dt_value


def coerce_date_value(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    date_value = coerce_datetime(value)
    if date_value:
        return date_value.date()

    text = cstr(value).strip()
    if not text:
        return None

    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def format_date_value(value):
    date_value = coerce_date_value(value)
    return date_value.isoformat() if date_value else ""


def has_value(value):
    if value is None:
        return False
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return bool(cstr(value).strip())


def normalize_match_text(value):
    text = cstr(value).strip().upper()
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(text.replace(".", " ").split())


def first_value(data, *keys):
    if not isinstance(data, dict):
        return None
    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return value
    return None


def extract_request_error(response):
    if not response:
        return _("Unknown error")
    try:
        payload = response.json() or {}
    except ValueError:
        payload = {}
    return (
        first_value(payload, "message", "error", "detail")
        or cstr(getattr(response, "text", ""))
        or _("Unknown error")
    )


def _resolve_customer_name(customer=None, tax_code=None):
    customer = cstr(customer).strip()
    if customer:
        return customer

    tax_code = normalize_tax_code(tax_code)
    if not tax_code:
        return ""

    for fieldname in _get_customer_tax_lookup_fields():
        customer_name = frappe.db.get_value("Customer", {fieldname: tax_code}, "name")
        if customer_name:
            return customer_name
    return ""


def _get_customer_tax_code(customer):
    customer = cstr(customer).strip()
    if not customer:
        return ""

    for fieldname in _get_customer_tax_lookup_fields():
        value = frappe.db.get_value("Customer", customer, fieldname)
        if cstr(value).strip():
            return value
    return ""


def _get_customer_tax_lookup_fields():
    fields = ["tax_id"]
    if _customer_has_field("tax_code"):
        fields.append("tax_code")
    return fields


def _customer_has_field(fieldname):
    fieldname = cstr(fieldname).strip()
    if not fieldname:
        return False

    if fieldname in STANDARD_CUSTOMER_FIELDS:
        return True

    has_column = getattr(getattr(frappe, "db", None), "has_column", None)
    if callable(has_column):
        try:
            return bool(has_column("Customer", fieldname))
        except Exception:
            return False

    return False


def _db_set_value(doctype, name, fieldname, value, update_modified=False):
    try:
        frappe.db.set_value(doctype, name, fieldname, value, update_modified=update_modified)
    except TypeError:
        frappe.db.set_value(doctype, name, fieldname, value)


def _get_default_customer_group():
    user_default = frappe.defaults.get_user_default("Customer Group")
    if user_default and frappe.db.exists("Customer Group", {"name": user_default, "is_group": 0}):
        return user_default

    for preferred in ("Commercial", "Individual"):
        if frappe.db.exists("Customer Group", {"name": preferred, "is_group": 0}):
            return preferred

    rows = frappe.get_all(
        "Customer Group",
        filters={"is_group": 0},
        fields=["name"],
        order_by="name asc",
        limit_page_length=1,
    )
    if not rows:
        return None
    first_row = rows[0]
    return first_row.name if hasattr(first_row, "name") else first_row.get("name")


def _get_default_territory():
    user_default = frappe.defaults.get_user_default("Territory")
    if user_default and frappe.db.exists("Territory", {"name": user_default, "is_group": 0}):
        return user_default

    for preferred in ("Vietnam", "Rest Of The World"):
        if frappe.db.exists("Territory", {"name": preferred, "is_group": 0}):
            return preferred

    rows = frappe.get_all(
        "Territory",
        filters={"is_group": 0},
        fields=["name"],
        order_by="name asc",
        limit_page_length=1,
    )
    if not rows:
        return None
    first_row = rows[0]
    return first_row.name if hasattr(first_row, "name") else first_row.get("name")


def _get_setting(site_key, env_key, default=None):
    conf = getattr(frappe, "conf", None) or {}
    value = None
    if hasattr(conf, "get"):
        value = conf.get(site_key)
    elif isinstance(conf, dict):
        value = conf.get(site_key)
    if value not in (None, ""):
        return value
    env_value = os.environ.get(env_key)
    if env_value not in (None, ""):
        return env_value
    return default

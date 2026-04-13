import json
from datetime import datetime, timezone

from frappe.model.document import Document
from frappe.utils import cint, cstr


LEVEL_ALIASES = {
    "LOW": "SAFE",
    "MEDIUM": "WARNING",
    "WARN": "WARNING",
    "DANGER": "HIGH",
}


def infer_risk_level(score, provided_level=None):
    normalized = LEVEL_ALIASES.get(cstr(provided_level).strip().upper(), cstr(provided_level).strip().upper())
    if normalized in {"SAFE", "WARNING", "HIGH"}:
        return normalized

    score = cint(score or 0)
    if score >= 70:
        return "HIGH"
    if score >= 40:
        return "WARNING"
    return "SAFE"


class CustomerRiskProfile(Document):
    def validate(self):
        self.tax_code = cstr(self.tax_code).strip().replace(" ", "")
        self.risk_score = cint(self.risk_score or 0)
        self.risk_level = infer_risk_level(self.risk_score, self.risk_level)
        self.last_check_date = coerce_datetime(self.last_check_date)

        if isinstance(self.reasons, (list, tuple)):
            self.reasons = "\n".join(cstr(row).strip() for row in self.reasons if cstr(row).strip())

        if self.raw_response and not isinstance(self.raw_response, str):
            self.raw_response = json.dumps(self.raw_response, ensure_ascii=False, indent=2, default=str)


def coerce_datetime(value):
    if not value:
        return value
    if isinstance(value, datetime):
        dt_value = value
    else:
        try:
            dt_value = datetime.fromisoformat(cstr(value).replace("Z", "+00:00"))
        except ValueError:
            return value

    if dt_value.tzinfo is not None:
        dt_value = dt_value.astimezone(timezone.utc).replace(tzinfo=None)
    return dt_value

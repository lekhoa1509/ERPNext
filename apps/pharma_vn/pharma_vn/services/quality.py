from datetime import datetime


VALID_BATCH_DECISIONS = {"Released", "Hold", "Rejected"}


def normalize_batch_decision(decision):
    # Chuan hoa gia tri de API, UI va integration ben ngoai dung cung 1 tap trang thai.
    normalized = str(decision or "").strip().title()
    if normalized not in VALID_BATCH_DECISIONS:
        raise ValueError("decision must be Released, Hold, or Rejected")
    return normalized


def build_batch_release_values(data, *, current_user, release_timestamp=None):
    decision = normalize_batch_decision(data.get("decision"))
    release_timestamp = release_timestamp or datetime.utcnow()

    # Tach phan "du lieu chung tu" va "du lieu cap nhat Batch" de API/hook co the tai su dung.
    release_values = {
        "batch_no": data["batch_no"],
        "item_code": data["item_code"],
        "warehouse": data.get("warehouse"),
        "source_doctype": data.get("source_doctype"),
        "source_name": data.get("source_name"),
        "quality_reference": data.get("quality_reference"),
        "status": decision,
        "reviewed_by": data.get("reviewed_by") or current_user,
        "release_date": data.get("release_date") or release_timestamp,
        "remarks": data.get("remarks"),
    }

    batch_updates = {"batch_status": decision}
    if decision == "Released":
        # Khi release thanh cong, xoa co temperature excursion de batch du dieu kien ban.
        batch_updates.update(
            {
                "released_by": current_user,
                "release_date": release_values["release_date"],
                "temperature_excursion_flag": 0,
            }
        )

    return {
        "decision": decision,
        "release_values": release_values,
        "batch_updates": batch_updates,
    }


def evaluate_temperature_reading(temperature_c, min_temp=0, max_temp=25):
    temperature = float(temperature_c)
    lower_bound = float(min_temp)
    upper_bound = float(max_temp)

    # Excursion duoc phan loai som de phuc vu dashboard, canh bao va guardrail QA.
    if temperature < lower_bound:
        excursion = "below_min"
    elif temperature > upper_bound:
        excursion = "above_max"
    else:
        excursion = "within_range"

    return {
        "temperature_c": temperature,
        "min_temp": lower_bound,
        "max_temp": upper_bound,
        "excursion": excursion,
        "action_required": 1 if excursion != "within_range" else 0,
    }


def build_temperature_log_values(data, *, recorded_at=None):
    evaluation = evaluate_temperature_reading(
        data["temperature_c"],
        min_temp=data.get("min_temp", 0),
        max_temp=data.get("max_temp", 25),
    )
    # Ban ghi temperature log can day du ca du lieu goc lan ket qua danh gia.
    log_values = {
        "warehouse": data["warehouse"],
        "item_code": data.get("item_code"),
        "batch_no": data.get("batch_no"),
        "sensor_id": data["sensor_id"],
        "recorded_at": data.get("recorded_at") or recorded_at,
        "temperature_c": evaluation["temperature_c"],
        "min_temp": evaluation["min_temp"],
        "max_temp": evaluation["max_temp"],
        "action_required": evaluation["action_required"],
        "excursion_type": evaluation["excursion"],
        "notes": data.get("notes"),
    }
    batch_updates = None
    if evaluation["action_required"] and data.get("batch_no"):
        # Neu vuot nguong va co batch, dua batch ve Hold ngay de chan xuat ban nham.
        batch_updates = {
            "batch_status": "Hold",
            "temperature_excursion_flag": 1,
        }
    return {
        "evaluation": evaluation,
        "log_values": log_values,
        "batch_updates": batch_updates,
    }


def build_recall_values(data, *, initiated_by, initiated_on, affected_delivery_count):
    status = str(data.get("status") or "Open").strip().title() or "Open"
    # So don giao anh huong duoc tinh truoc va dong bang vao case de phuc vu truy vet.
    return {
        "company": data["company"],
        "item_code": data["item_code"],
        "batch_no": data["batch_no"],
        "reason": data["reason"],
        "status": status,
        "initiated_by": initiated_by,
        "initiated_on": initiated_on,
        "affected_delivery_count": int(affected_delivery_count or 0),
        "notes": data.get("notes"),
    }

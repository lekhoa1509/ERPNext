import json
import logging
from pathlib import Path


LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
LOG_FILE = LOG_DIR / "pharma_operations.log"


def get_operations_logger():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("pharma_vn.operations")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def build_alert_event(*, alert_type, message, severity="Medium", reference_doctype=None, reference_name=None, payload=None):
    return {
        "alert_type": alert_type,
        "severity": severity,
        "message": message,
        "reference_doctype": reference_doctype,
        "reference_name": reference_name,
        "payload_json": json.dumps(payload or {}, ensure_ascii=False, sort_keys=True),
    }


def make_alert_key(alert_type, reference_name=None, reference_doctype=None, suffix=None):
    return "|".join(
        str(value or "-")
        for value in (alert_type, reference_doctype, reference_name, suffix)
    )


def detect_stock_mismatch_rows(rows, tolerance=0.0001):
    mismatches = []
    for row in rows or []:
        cell_qty = float(row.get("cell_qty") or 0)
        bin_qty = float(row.get("bin_qty") or 0)
        difference = round(cell_qty - bin_qty, 4)
        if abs(difference) <= tolerance:
            continue
        mismatches.append(
            {
                "warehouse": row.get("warehouse"),
                "item_code": row.get("item_code"),
                "cell_qty": cell_qty,
                "bin_qty": bin_qty,
                "difference": difference,
            }
        )
    return mismatches

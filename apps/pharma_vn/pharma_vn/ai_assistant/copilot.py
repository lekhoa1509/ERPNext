import re


WORKFLOW_DEFINITIONS = {
    "batch_release": {
        "label": "PH Batch Release",
        "keywords": ("batch release", "qa release", "release batch", "giai phong lo", "release lo"),
        "steps": [
            "Xac nhan batch, item, kho va chung tu nguon.",
            "Kiem tra COA/QA reference va quyet dinh Released, Hold hoac Rejected.",
            "Cap nhat Batch Status va ghi dau vet nguoi phe duyet.",
        ],
        "required_fields": ["batch_no", "item_code", "decision"],
    },
    "recall_case": {
        "label": "Recall",
        "keywords": ("recall", "thu hoi", "truy vet lo", "goi thu hoi"),
        "steps": [
            "Xac nhan item, batch va ly do thu hoi.",
            "Thong ke cac Delivery Note da giao co batch bi anh huong.",
            "Chuyen batch sang trang thai Recalled va mo case xu ly.",
        ],
        "required_fields": ["company", "item_code", "batch_no", "reason"],
    },
    "temperature_excursion": {
        "label": "Temperature Log",
        "keywords": ("temperature", "nhiet do", "cold chain", "excursion"),
        "steps": [
            "Ghi nhan kho, sensor, batch va gia tri nhiet do.",
            "So sanh voi nguong min/max de xac dinh excursion.",
            "Neu vuot nguong, dua batch ve Hold de QA review.",
        ],
        "required_fields": ["warehouse", "sensor_id", "temperature_c"],
    },
    "invoice_compliance": {
        "label": "E-Invoice + VAT",
        "keywords": ("e-invoice", "hoa don dien tu", "vat", "thue", "invoice compliance"),
        "steps": [
            "Kiem tra company, customer, ma so thue va ngay posting.",
            "Rao soat thue suat VAT tren tung dong va tong hop VAT.",
            "Chi issue hoa don dien tu khi guardrail dat trang thai ready/review.",
        ],
        "required_fields": ["company", "customer", "posting_date"],
    },
}


def detect_copilot_workflow(message):
    normalized = normalize_text(message)
    for workflow_key, definition in WORKFLOW_DEFINITIONS.items():
        if any(keyword in normalized for keyword in definition["keywords"]):
            return workflow_key
    return None


def build_copilot_reply(workflow_key):
    definition = WORKFLOW_DEFINITIONS[workflow_key]
    step_lines = [f"{index}. {step}" for index, step in enumerate(definition["steps"], start=1)]
    required = ", ".join(definition["required_fields"])
    return (
        f"Co the chay workflow `{definition['label']}` theo 3 buoc.\n"
        + "\n".join(step_lines)
        + f"\nThong tin can chuan bi: {required}."
    )


def normalize_text(value):
    return re.sub(r"\s+", " ", str(value or "").strip().lower())

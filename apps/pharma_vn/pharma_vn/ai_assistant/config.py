import os


def _get_bool(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    return str(value).strip().lower() not in {"0", "false", "no", "off", ""}


ENABLED = _get_bool("AI_ASSISTANT_ENABLED", True)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1").strip() or "gpt-4.1"

DEFAULT_COMPANY = os.getenv("AI_DEFAULT_COMPANY", "Viet An Pharma JSC").strip()
DEFAULT_WAREHOUSE = os.getenv("AI_DEFAULT_WAREHOUSE", "HCM Sellable - VAP").strip()
DEFAULT_REPORT_RECIPIENTS = os.getenv(
    "AI_DEFAULT_REPORT_RECIPIENTS",
    "admin@example.com",
).strip()

SYSTEM_PROMPT = os.getenv("AI_SYSTEM_PROMPT", "").strip()

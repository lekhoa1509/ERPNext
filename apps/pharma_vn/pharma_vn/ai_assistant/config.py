import os


DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"


def _get_bool(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    return str(value).strip().lower() not in {"0", "false", "no", "off", ""}


def _get_first(*names, default=""):
    for name in names:
        value = os.getenv(name)
        if value is None:
            continue
        cleaned = str(value).strip()
        if cleaned:
            return cleaned
    return default


def _get_api_base_url():
    configured = _get_first("OPENAI_BASE_URL")
    if configured:
        return configured.rstrip("/")
    return DEFAULT_OPENAI_BASE_URL


def _get_model():
    configured = _get_first("OPENAI_MODEL", "AI_MODEL")
    if configured:
        return configured
    return DEFAULT_OPENAI_MODEL


ENABLED = _get_bool("AI_ASSISTANT_ENABLED", True)
API_KEY = _get_first("OPENAI_API_KEY")
OPENAI_API_KEY = API_KEY
API_BASE_URL = _get_api_base_url()
OPENAI_BASE_URL = API_BASE_URL
MODEL = _get_model()
OPENAI_MODEL = MODEL
PROVIDER_NAME = "OpenAI"
API_KEY_ENV_VAR = "OPENAI_API_KEY"

DEFAULT_COMPANY = os.getenv("AI_DEFAULT_COMPANY", "Viet An Pharma JSC").strip()
DEFAULT_WAREHOUSE = os.getenv("AI_DEFAULT_WAREHOUSE", "HCM Sellable - VAP").strip()
DEFAULT_REPORT_RECIPIENTS = os.getenv(
    "AI_DEFAULT_REPORT_RECIPIENTS",
    "admin@example.com",
).strip()

SYSTEM_PROMPT = os.getenv("AI_SYSTEM_PROMPT", "").strip()

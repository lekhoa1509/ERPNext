import importlib
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

APP_ROOT = Path(__file__).resolve().parents[2]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from pharma_vn.ai_assistant import config as assistant_config


class AIAssistantConfigTest(unittest.TestCase):
    def tearDown(self):
        importlib.reload(assistant_config)

    def test_uses_openai_defaults_when_api_key_present(self):
        with patch.dict(
            os.environ,
            {
                "AI_ASSISTANT_ENABLED": "1",
                "OPENAI_API_KEY": "openai-test-key",
            },
            clear=True,
        ):
            config = importlib.reload(assistant_config)
            self.assertEqual(config.API_KEY, "openai-test-key")
            self.assertEqual(config.API_BASE_URL, "https://api.openai.com/v1")
            self.assertEqual(config.MODEL, "gpt-4.1-mini")
            self.assertEqual(config.PROVIDER_NAME, "OpenAI")
            self.assertEqual(config.API_KEY_ENV_VAR, "OPENAI_API_KEY")

    def test_respects_openai_base_url_and_model_overrides(self):
        with patch.dict(
            os.environ,
            {
                "AI_ASSISTANT_ENABLED": "1",
                "OPENAI_API_KEY": "openai-test-key",
                "OPENAI_BASE_URL": "https://example-proxy.invalid/v1",
                "OPENAI_MODEL": "gpt-4.1",
            },
            clear=True,
        ):
            config = importlib.reload(assistant_config)
            self.assertEqual(config.API_KEY, "openai-test-key")
            self.assertEqual(config.API_BASE_URL, "https://example-proxy.invalid/v1")
            self.assertEqual(config.MODEL, "gpt-4.1")
            self.assertEqual(config.PROVIDER_NAME, "OpenAI")
            self.assertEqual(config.API_KEY_ENV_VAR, "OPENAI_API_KEY")


if __name__ == "__main__":
    unittest.main()

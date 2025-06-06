"""
Tests for the settings module
"""

import os
import sys
from unittest.mock import patch

from pydantic_settings import SettingsConfigDict

# Add src directory to path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from config.settings import Settings


class TestSettings:
    """Tests for settings."""

    def test_settings_default_values(self):
        """Test default values in settings."""
        # We need to patch the Settings class's model_config to avoid loading from .env
        with (
            patch.object(
                Settings, "model_config", SettingsConfigDict(env_ignore_env_file=True)
            ),
            patch.dict(os.environ, {}, clear=True),
        ):
            # Create settings with no environment variables
            settings = Settings()

            # Check default values
            assert settings.GEMINI_API_KEY == ""
            assert settings.NOTION_API_KEY == ""
            assert settings.NOTION_DATABASE_ID == ""
            assert settings.GEMINI_MODEL == "gemini-2.0-flash"
            assert settings.TEMPERATURE == 0.0
            assert settings.TIMEZONE == "UTC"

    def test_settings_from_env_variables(self):
        """Test loading settings from environment variables."""
        mock_env = {
            "GEMINI_API_KEY": "test_gemini_key",
            "NOTION_API_KEY": "test_notion_key",
            "NOTION_DATABASE_ID": "test_db_id",
            "GEMINI_MODEL": "custom_model",
            "TEMPERATURE": "0.8",
            "TIMEZONE": "Europe/Paris",
        }

        # We need to patch the Settings class's model_config to avoid loading from .env
        with (
            patch.object(
                Settings, "model_config", SettingsConfigDict(env_ignore_env_file=True)
            ),
            patch.dict(os.environ, mock_env, clear=True),
        ):
            # Create settings with environment variables
            settings = Settings()

            # Check values loaded from environment
            assert settings.GEMINI_API_KEY == "test_gemini_key"
            assert settings.NOTION_API_KEY == "test_notion_key"
            assert settings.NOTION_DATABASE_ID == "test_db_id"
            assert settings.GEMINI_MODEL == "custom_model"
            assert settings.TEMPERATURE == 0.8
            assert settings.TIMEZONE == "Europe/Paris"

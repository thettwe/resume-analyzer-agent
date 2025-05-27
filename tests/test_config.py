"""
Tests for the config module
"""

import os
import sys
from unittest.mock import MagicMock, mock_open, patch

import pytest

# Add src directory to path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from config.config import create_env_example, get_config


class TestConfig:
    """Tests for configuration functions."""

    def test_get_config_all_values_from_env(self):
        """Test loading config with all values from environment."""
        # Use a fresh MagicMock to avoid interference from environment variables
        mock_settings = MagicMock()
        mock_settings.GEMINI_API_KEY = "env_gemini_key"
        mock_settings.NOTION_API_KEY = "env_notion_key"
        mock_settings.NOTION_DATABASE_ID = "env_notion_db"
        mock_settings.GEMINI_MODEL = "env_gemini_model"
        mock_settings.TEMPERATURE = 0.7
        mock_settings.TIMEZONE = "Europe/London"

        # Mock the settings module
        with patch("config.config.settings", mock_settings):
            # Call the function
            config = get_config()

            # Verify the result
            assert config["GEMINI_API_KEY"] == "env_gemini_key"
            assert config["NOTION_API_KEY"] == "env_notion_key"
            assert config["NOTION_DATABASE_ID"] == "env_notion_db"
            assert config["GEMINI_MODEL"] == "env_gemini_model"
            assert config["TEMPERATURE"] == 0.7
            assert config["TIMEZONE"] == "Europe/London"

    def test_get_config_with_cli_overrides(self):
        """Test loading config with CLI overrides."""
        # Use a fresh MagicMock to avoid interference from environment variables
        mock_settings = MagicMock()
        mock_settings.GEMINI_API_KEY = "env_gemini_key"
        mock_settings.NOTION_API_KEY = "env_notion_key"
        mock_settings.NOTION_DATABASE_ID = "env_notion_db"
        mock_settings.GEMINI_MODEL = "env_gemini_model"
        mock_settings.TEMPERATURE = 0.7
        mock_settings.TIMEZONE = "Europe/London"

        # Mock the settings module
        with patch("config.config.settings", mock_settings):
            # Call the function with CLI overrides
            config = get_config(
                cli_notion_db_id="cli_notion_db",
                cli_notion_api_key="cli_notion_key",
                cli_gemini_api_key="cli_gemini_key",
                cli_gemini_model="cli_gemini_model",
                cli_temperature=0.2,
                cli_timezone="America/New_York",
            )

            # Verify the result
            assert config["GEMINI_API_KEY"] == "cli_gemini_key"
            assert config["NOTION_API_KEY"] == "cli_notion_key"
            assert config["NOTION_DATABASE_ID"] == "cli_notion_db"
            assert config["GEMINI_MODEL"] == "cli_gemini_model"
            assert config["TEMPERATURE"] == 0.2
            assert config["TIMEZONE"] == "America/New_York"

    def test_get_config_missing_required_values(self):
        """Test error when required config values are missing."""
        # Use a fresh MagicMock to avoid interference from environment variables
        mock_settings = MagicMock()
        mock_settings.GEMINI_API_KEY = ""
        mock_settings.NOTION_API_KEY = "env_notion_key"
        mock_settings.NOTION_DATABASE_ID = ""
        mock_settings.GEMINI_MODEL = "env_gemini_model"
        mock_settings.TEMPERATURE = 0.7
        mock_settings.TIMEZONE = "UTC"

        # Mock the settings module
        with patch("config.config.settings", mock_settings):
            # Call the function and expect ValueError
            with pytest.raises(ValueError) as exc_info:
                get_config()

            # Verify error message contains missing keys
            error_msg = str(exc_info.value)
            assert "Missing required configuration" in error_msg
            assert "GEMINI_API_KEY" in error_msg
            assert "NOTION_DATABASE_ID" in error_msg

    def test_create_env_example(self):
        """Test creating .env.example file."""
        # Mock the open function
        mock_file = mock_open()

        # We need to mock rprint separately since it's imported directly
        with (
            patch("builtins.open", mock_file),
            patch("config.config.rprint") as mock_rprint,
        ):
            # Call the function
            create_env_example()

            # Verify file creation
            mock_file.assert_called_once_with(".env.example", "w")

            # Check file content
            written_content = mock_file().write.call_args[0][0]
            assert "GEMINI_API_KEY=" in written_content
            assert "NOTION_API_KEY=" in written_content
            assert "NOTION_DATABASE_ID=" in written_content
            assert "GEMINI_MODEL=" in written_content
            assert "TEMPERATURE=" in written_content
            assert "TIMEZONE=" in written_content

            # Verify success message
            mock_rprint.assert_called_once()
            assert "Created .env.example file successfully" in str(
                mock_rprint.call_args[0][0]
            )

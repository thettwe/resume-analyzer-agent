"""
Tests for the main app module
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from rich.panel import Panel
from typer.testing import CliRunner

# Add src directory to path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from app import app, main, process, setup


class TestApp:
    """Tests for the main app."""

    runner = CliRunner()

    def test_main_without_command(self):
        """Test main function without subcommand."""
        with patch("app.rprint") as mock_print:
            # Create a mock context
            ctx = MagicMock()
            ctx.invoked_subcommand = None

            # Call the function
            main(ctx)

            # Verify that rprint was called with the welcome panel
            mock_print.assert_called_once()
            panel_arg = mock_print.call_args[0][0]
            assert isinstance(panel_arg, Panel)
            assert "Resume Analyzer Agent" in str(panel_arg.title)

    def test_setup_command(self):
        """Test setup command."""
        with patch("app.setup_command") as mock_setup:
            # Call the function
            setup()

            # Verify that setup_command was called
            mock_setup.assert_called_once()

    def test_process_command(self):
        """Test process command."""
        with patch("app.asyncio.run") as mock_run:
            # Don't try to check what's passed to asyncio.run
            # Just verify it was called

            # Call the function
            process(
                cv_folder="test_folder",
                jd_file="test.pdf",
                notion_db_id="test_db",
                notion_api_key="test_api_key",
                gemini_api_key="test_gemini_key",
                gemini_model="test_model",
                gemini_temperature=0.5,
                max_gemini_concurrent=5,
                max_notion_concurrent=3,
            )

            # Verify asyncio.run was called (without checking arguments)
            assert mock_run.call_count == 1

    @pytest.mark.parametrize(
        "command,expected_exit_code",
        [
            (["--help"], 0),
            (["setup"], 0),
        ],
    )
    def test_cli_commands(self, command, expected_exit_code):
        """Test CLI commands using CliRunner."""
        with patch("app.setup_command"):
            result = self.runner.invoke(app, command)
            assert result.exit_code == expected_exit_code

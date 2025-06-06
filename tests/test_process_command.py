"""
Tests for the process command module
"""

import os
import sys
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest
import typer

# Add src directory to path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from commands.process import process_command


class TestProcessCommand:
    """Tests for process command."""

    @pytest.mark.asyncio
    @patch("commands.process.extract_text_from_pdf")
    @patch("commands.process.get_cv_files")
    @patch("commands.process.format_cv_files")
    @patch("commands.process.extract_cv_text")
    @patch("commands.process.process_with_gemini")
    @patch("commands.process.upload_to_notion")
    @patch("commands.process.format_processing_stats")
    @patch("commands.process.NotionManager")
    @patch("commands.process.genai.Client")
    @patch("commands.process.verify_gemini_api_key")
    @patch("commands.process.get_config")
    @patch("commands.process.rprint")
    async def test_process_command_success(
        self,
        mock_rprint,
        mock_get_config,
        mock_verify_gemini,
        mock_gemini_client,
        mock_notion_manager,
        mock_format_stats,
        mock_upload,
        mock_process,
        mock_extract,
        mock_format_cv_files,
        mock_get_files,
        mock_extract_pdf,
    ):
        """Test successful process command execution."""
        # Setup mocks
        mock_get_config.return_value = {
            "GEMINI_API_KEY": "test_key",
            "NOTION_API_KEY": "test_key",
            "NOTION_DATABASE_ID": "test_db",
            "GEMINI_MODEL": "test_model",
            "TEMPERATURE": 0.5,
            "TIMEZONE": "UTC",
        }
        mock_extract_pdf.return_value = "JD Text"

        mock_get_files.return_value = ["cv1.pdf", "cv2.pdf"]
        mock_format_cv_files.return_value = [
            {"file_path": "cv1.pdf", "file_name": "cv1.pdf"},
            {"file_path": "cv2.pdf", "file_name": "cv2.pdf"},
        ]

        mock_extract.return_value = [
            {"file_name": "cv1.pdf", "text": "CV 1 Text"},
            {"file_name": "cv2.pdf", "text": "CV 2 Text"},
        ]

        mock_process.return_value = [MagicMock(), MagicMock()]
        mock_upload.return_value = (2, 0, 0)  # successful, duplicate, failed
        mock_format_stats.return_value = "Stats"

        # Mock NotionManager
        notion_instance = AsyncMock()
        notion_instance.configure.return_value = notion_instance
        mock_notion_manager.return_value = notion_instance

        # Set up patch for os.path.exists and os.listdir
        with (
            patch("os.path.exists", return_value=True),
            patch("os.listdir", return_value=["cv1.pdf", "cv2.pdf"]),
        ):
            # Call function
            await process_command(
                cv_folder="test_folder",
                jd_file="test_jd.pdf",
                notion_db_id="test_db",
                notion_api_key="test_key",
                gemini_api_key="test_key",
                gemini_model="test_model",
                gemini_temperature=0.5,
                max_gemini_concurrent=5,
                max_notion_concurrent=3,
                timezone="Europe/London",
            )

        # Verify calls
        mock_get_config.assert_called_once_with(
            "test_db", "test_key", "test_key", "test_model", 0.5, "Europe/London"
        )
        mock_verify_gemini.assert_called_once_with("test_key")
        mock_gemini_client.assert_called_once_with(api_key="test_key")

        # Verify NotionManager was initialized with timezone
        mock_notion_manager.assert_called_once_with(
            token="test_key", database_id="test_db", timezone="UTC"
        )

        mock_extract_pdf.assert_called_once_with("test_jd.pdf")
        mock_get_files.assert_called_once_with("test_folder")
        mock_format_cv_files.assert_called_once()
        mock_extract.assert_called_once()
        mock_process.assert_called_once()
        mock_upload.assert_called_once()
        mock_format_stats.assert_called_once()

    @pytest.mark.asyncio
    @patch("commands.process.rprint")
    async def test_process_command_missing_folder(self, mock_rprint):
        """Test process command with missing CV folder."""
        with pytest.raises(ValueError) as excinfo:
            await process_command(
                cv_folder="nonexistent_folder",
                jd_file="test.pdf",
                notion_db_id=None,
                notion_api_key=None,
                gemini_api_key=None,
                gemini_model=None,
                gemini_temperature=None,
            )

        assert "CV folder not found" in str(excinfo.value)

    @pytest.mark.asyncio
    @patch("commands.process.get_cv_files")
    @patch("commands.process.rprint")
    @patch("os.path.exists")
    @patch("os.listdir")
    async def test_process_command_no_cv_files(
        self, mock_listdir, mock_exists, mock_rprint, mock_get_files
    ):
        """Test process command with no CV files."""
        # Setup mocks
        mock_exists.return_value = True
        mock_listdir.return_value = ["file1.txt", "file2.jpg"]
        mock_get_files.return_value = []

        with pytest.raises(typer.Exit):
            await process_command(
                cv_folder="test_folder",
                jd_file="test.pdf",
                notion_db_id=None,
                notion_api_key=None,
                gemini_api_key=None,
                gemini_model=None,
                gemini_temperature=None,
            )

        mock_rprint.assert_called_with(
            ANY
        )  # Check if rprint was called with any argument

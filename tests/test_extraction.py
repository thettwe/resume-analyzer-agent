"""
Tests for core extraction functionality
"""

import os
import sys
import time
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console

# Add src directory to path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from core.extraction import extract_cv_text


class TestExtraction:
    """Tests for core extraction functionality."""

    @pytest.fixture
    def mock_console(self):
        """Create a mock console for testing."""
        mock = MagicMock(spec=Console)
        # Add get_time method needed by Progress
        mock.get_time = MagicMock(return_value=time.monotonic())
        # Add attributes needed by Progress
        mock.is_jupyter = False
        mock.is_interactive = False
        # Mock the print method for assertions
        mock.print = MagicMock()
        return mock

    @pytest.mark.asyncio
    @patch("core.extraction.extract_text_from_file")
    @patch(
        "core.extraction.rprint"
    )  # Mock rich print to avoid console output during tests
    async def test_extract_cv_text_success(
        self, mock_rprint, mock_extract, mock_console
    ):
        """Test successful CV text extraction."""
        # Setup mock
        mock_extract.return_value = "CV content"

        # Sample CV files
        cv_files = [
            {
                "file_name": "cv1.pdf",
                "file_path": "path/to/cv1.pdf",
            },
            {
                "file_name": "cv2.docx",
                "file_path": "path/to/cv2.docx",
            },
        ]

        # Execute
        result = await extract_cv_text(cv_files, mock_console)

        # Assert
        assert len(result) == 2
        assert result[0]["file_name"] == "cv1.pdf"
        assert result[0]["text"] == "CV content"
        assert result[1]["file_name"] == "cv2.docx"
        assert result[1]["text"] == "CV content"

        # Verify extraction calls
        assert mock_extract.call_count == 2

    @pytest.mark.asyncio
    @patch("core.extraction.extract_text_from_file")
    @patch(
        "core.extraction.rprint"
    )  # Mock rich print to avoid console output during tests
    async def test_extract_cv_text_empty_content(
        self, mock_rprint, mock_extract, mock_console
    ):
        """Test CV text extraction with empty content."""
        # Setup mock
        mock_extract.return_value = ""

        # Sample CV files
        cv_files = [
            {
                "file_name": "empty.pdf",
                "file_path": "path/to/empty.pdf",
            },
        ]

        # Execute
        result = await extract_cv_text(cv_files, mock_console)

        # Assert
        assert len(result) == 0
        mock_extract.assert_called_once_with("path/to/empty.pdf")
        # Verify empty content message
        assert any(
            "Empty text extracted" in str(args)
            for args, _ in mock_rprint.call_args_list
        )

    @pytest.mark.asyncio
    @patch("core.extraction.extract_text_from_file")
    @patch(
        "core.extraction.rprint"
    )  # Mock rich print to avoid console output during tests
    async def test_extract_cv_text_with_error(
        self, mock_rprint, mock_extract, mock_console
    ):
        """Test CV text extraction with an error."""
        # Setup mock to raise an exception
        mock_extract.side_effect = Exception("Extraction error")

        # Sample CV files
        cv_files = [
            {
                "file_name": "problematic.pdf",
                "file_path": "path/to/problematic.pdf",
            },
        ]

        # Execute
        result = await extract_cv_text(cv_files, mock_console)

        # Assert
        assert len(result) == 0
        mock_extract.assert_called_once_with("path/to/problematic.pdf")
        # Verify error message
        assert any(
            "Error extracting text" in str(args)
            for args, _ in mock_rprint.call_args_list
        )

    @pytest.mark.asyncio
    @patch(
        "core.extraction.rprint"
    )  # Mock rich print to avoid console output during tests
    async def test_extract_cv_text_empty_input(self, mock_rprint, mock_console):
        """Test CV text extraction with empty input."""
        # Execute
        result = await extract_cv_text([], mock_console)

        # Assert
        assert result == []

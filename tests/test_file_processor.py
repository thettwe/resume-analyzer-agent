"""
Tests for file processor module
"""

import os
import sys
from unittest.mock import MagicMock, patch

# Add src directory to path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from misc.file_processor import (
    extract_text_from_docx,
    extract_text_from_pdf,
    format_cv_files,
    get_cv_files,
)


class TestFileProcessor:
    """Tests for file processor functions."""

    @patch("misc.file_processor.Document")
    def test_extract_text_from_docx(self, mock_document):
        """Test extracting text from a DOCX file."""
        # Setup mock document
        mock_para1 = MagicMock()
        mock_para1.text = "Paragraph 1"
        mock_para2 = MagicMock()
        mock_para2.text = "Paragraph 2"

        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para1, mock_para2]
        mock_document.return_value = mock_doc

        # Mock file existence check
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True

            # Execute
            result = extract_text_from_docx("dummy.docx")

            # Assert
            assert result == "Paragraph 1\nParagraph 2"
            mock_document.assert_called_once_with("dummy.docx")

    @patch("pdfplumber.open")
    def test_extract_text_from_pdf(self, mock_pdf_open):
        """Test extracting text from a PDF file."""
        # Setup mock PDF
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1 content"
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Page 2 content"

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.__exit__.return_value = None

        mock_pdf_open.return_value = mock_pdf

        # Mock file existence check
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True

            # Execute
            result = extract_text_from_pdf("dummy.pdf")

            # Assert
            assert result == "Page 1 content\nPage 2 content"
            mock_pdf_open.assert_called_once_with("dummy.pdf")

    @patch("os.path.isfile")
    @patch("os.listdir")
    @patch("os.path.exists")
    def test_get_cv_files(self, mock_exists, mock_listdir, mock_isfile):
        """Test getting CV files from a folder."""
        # Setup mocks
        mock_exists.return_value = True
        mock_listdir.return_value = ["cv1.pdf", "cv2.docx", "notes.txt", "image.jpg"]

        # Make only the PDF and DOCX files return True for isfile
        def is_file_side_effect(path):
            return path.endswith((".pdf", ".docx"))

        mock_isfile.side_effect = is_file_side_effect

        # Execute
        result = get_cv_files("dummy_folder")

        # Assert
        assert len(result) == 2
        assert os.path.join("dummy_folder", "cv1.pdf") in result
        assert os.path.join("dummy_folder", "cv2.docx") in result
        assert os.path.join("dummy_folder", "notes.txt") not in result
        assert os.path.join("dummy_folder", "image.jpg") not in result

    @patch("os.path.isfile")
    @patch("os.listdir")
    def test_get_cv_files_empty_folder(self, mock_listdir, mock_isfile):
        """Test getting CV files from an empty folder."""
        # Setup mocks
        mock_listdir.return_value = []
        mock_isfile.return_value = False

        # Execute
        result = get_cv_files("dummy_folder")

        # Assert
        assert result == []

    @patch("os.path.isfile")
    @patch("os.listdir")
    def test_get_cv_files_no_supported_files(self, mock_listdir, mock_isfile):
        """Test getting CV files from a folder with no supported files."""
        # Setup mocks
        mock_listdir.return_value = ["notes.txt", "image.jpg"]
        mock_isfile.return_value = True

        # Execute
        result = get_cv_files("dummy_folder")

        # Assert
        assert result == []

    def test_format_cv_files(self):
        """Test formatting CV file paths into dictionaries."""
        # Sample input
        file_paths = [
            "/path/to/cv1.pdf",
            "/path/to/subdir/cv2.docx",
        ]

        # Execute
        result = format_cv_files(file_paths)

        # Assert
        assert len(result) == 2
        assert result[0]["file_path"] == "/path/to/cv1.pdf"
        assert result[0]["file_name"] == "cv1.pdf"
        assert result[1]["file_path"] == "/path/to/subdir/cv2.docx"
        assert result[1]["file_name"] == "cv2.docx"

    def test_format_cv_files_empty_list(self):
        """Test formatting an empty list of CV file paths."""
        # Execute
        result = format_cv_files([])

        # Assert
        assert result == []

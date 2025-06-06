"""
Tests for the file extraction functionality
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Add src directory to path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from misc.file_processor import (
    extract_text_from_docx,
    extract_text_from_file,
    extract_text_from_pdf,
)


class TestFileExtraction:
    """Tests for file extraction functionality."""

    @patch("misc.file_processor.pdfplumber.open")
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

    @patch("misc.file_processor.pdfplumber.open")
    def test_extract_text_from_empty_pdf(self, mock_pdf_open):
        """Test extracting text from an empty PDF file."""
        # Setup mock empty PDF
        mock_pdf = MagicMock()
        mock_pdf.pages = []
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.__exit__.return_value = None

        mock_pdf_open.return_value = mock_pdf

        # Mock file existence check
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True

            # Execute
            result = extract_text_from_pdf("empty.pdf")

            # Assert
            assert result == ""
            mock_pdf_open.assert_called_once_with("empty.pdf")

    @patch("misc.file_processor.pdfplumber.open")
    def test_extract_text_from_pdf_with_error(self, mock_pdf_open):
        """Test extracting text from a PDF with extraction errors."""
        # Setup mock to raise an exception
        mock_pdf_open.side_effect = Exception("PDF error")

        # Mock file existence check
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True

            # Execute and assert
            with pytest.raises(ValueError) as excinfo:
                extract_text_from_pdf("problematic.pdf")

            assert "Error extracting text from PDF" in str(excinfo.value)
            mock_pdf_open.assert_called_once_with("problematic.pdf")

    def test_extract_text_from_pdf_file_not_found(self):
        """Test extracting text from a non-existent PDF file."""
        # Mock file existence check
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = False

            with pytest.raises(FileNotFoundError) as excinfo:
                extract_text_from_pdf("nonexistent.pdf")
            assert "PDF file not found" in str(excinfo.value)

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

    @patch("misc.file_processor.Document")
    def test_extract_text_from_empty_docx(self, mock_document):
        """Test extracting text from an empty DOCX file."""
        # Setup mock empty document
        mock_doc = MagicMock()
        mock_doc.paragraphs = []
        mock_document.return_value = mock_doc

        # Mock file existence check
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True

            # Execute
            result = extract_text_from_docx("empty.docx")

            # Assert
            assert result == ""
            mock_document.assert_called_once_with("empty.docx")

    @patch("misc.file_processor.Document")
    def test_extract_text_from_docx_with_error(self, mock_document):
        """Test extracting text from a DOCX with extraction errors."""
        # Setup mock to raise an exception
        mock_document.side_effect = Exception("DOCX error")

        # Mock file existence check
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True

            # Execute and assert
            with pytest.raises(ValueError) as excinfo:
                extract_text_from_docx("problematic.docx")

            assert "Error extracting text from DOCX" in str(excinfo.value)
            mock_document.assert_called_once_with("problematic.docx")

    def test_extract_text_from_docx_file_not_found(self):
        """Test extracting text from a non-existent DOCX file."""
        # Mock file existence check
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = False

            with pytest.raises(FileNotFoundError) as excinfo:
                extract_text_from_docx("nonexistent.docx")
            assert "DOCX file not found" in str(excinfo.value)

    @patch("misc.file_processor.extract_text_from_pdf")
    def test_extract_text_from_file_pdf(self, mock_extract_pdf):
        """Test extract_text_from_file with PDF."""
        mock_extract_pdf.return_value = "PDF content"
        result = extract_text_from_file("test.pdf")
        assert result == "PDF content"
        mock_extract_pdf.assert_called_once_with("test.pdf")

    @patch("misc.file_processor.extract_text_from_docx")
    def test_extract_text_from_file_docx(self, mock_extract_docx):
        """Test extract_text_from_file with DOCX."""
        mock_extract_docx.return_value = "DOCX content"
        result = extract_text_from_file("test.docx")
        assert result == "DOCX content"
        mock_extract_docx.assert_called_once_with("test.docx")

    def test_extract_text_from_file_unsupported(self):
        """Test extract_text_from_file with unsupported file type."""
        with pytest.raises(ValueError) as excinfo:
            extract_text_from_file("test.txt")
        assert "Unsupported file type: txt" in str(excinfo.value)

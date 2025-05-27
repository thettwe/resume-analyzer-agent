"""
File processing utilities.
"""

import logging
import os
from typing import Dict, List

import pdfplumber
from docx import Document

logging.getLogger("pdfminer").setLevel(logging.ERROR)


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text content from a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Extracted text as a string

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file is password-protected or corrupted
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    try:
        with pdfplumber.open(pdf_path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception as e:
        raise ValueError(f"Error extracting text from PDF: {str(e)}")


def extract_text_from_docx(docx_path: str) -> str:
    """
    Extract text content from a DOCX file.

    Args:
        docx_path: Path to the DOCX file

    Returns:
        Extracted text as a string

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file is corrupted
    """
    if not os.path.exists(docx_path):
        raise FileNotFoundError(f"DOCX file not found: {docx_path}")
    try:
        doc = Document(docx_path)
        return "\n".join(paragraph.text for paragraph in doc.paragraphs)
    except Exception as e:
        raise ValueError(f"Error extracting text from DOCX: {str(e)}")


def get_cv_files(folder_path: str) -> List[str]:
    """
    Get all CV/JD files (PDF, DOCX) from the specified folder.

    Args:
        folder_path: Path to the folder containing CV files

    Returns:
        List of CV file paths

    Raises:
        FileNotFoundError: If the folder doesn't exist
    """
    if not os.path.exists(folder_path):
        return []

    cv_files = []
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        # Check if it's a file and has the right extension
        if os.path.isfile(file_path) and filename.lower().endswith((".pdf", ".docx")):
            cv_files.append(file_path)

    return cv_files


def format_cv_files(file_paths: List[str]) -> List[Dict[str, str]]:
    """
    Format file paths into dictionaries with file_path and file_name keys.

    Args:
        file_paths: List of file paths

    Returns:
        List of dictionaries with file_path and file_name keys
    """
    return [
        {"file_path": file_path, "file_name": os.path.basename(file_path)}
        for file_path in file_paths
    ]


def extract_text_from_file(file_path: str) -> str:
    """
    Extract text from a file based on its type.

    Args:
        file_path: Path to the file

    Returns:
        Extracted text as a string

    Raises:
        ValueError: If the file type is not supported
    """
    if file_path.lower().endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    elif file_path.lower().endswith(".docx"):
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path.split('.')[-1]}")

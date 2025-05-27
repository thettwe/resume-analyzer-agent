"""
Shared fixtures for tests
"""

import os
import time
from unittest.mock import AsyncMock, MagicMock

import pytest
from rich.console import Console

# Set environment variables for testing
os.environ["GEMINI_API_KEY"] = "test_gemini_api_key"
os.environ["GEMINI_MODEL"] = "gemini-2.0-flash"
os.environ["TEMPERATURE"] = "0.0"
os.environ["NOTION_API_KEY"] = "test_notion_api_key"
os.environ["NOTION_DATABASE_ID"] = "test_notion_database_id"
os.environ["TIMEZONE"] = "UTC"


@pytest.fixture
def sample_cv_text():
    """Sample CV text for testing."""
    return """
    John Doe
    Software Engineer
    
    Email: john.doe@example.com
    Phone: +1234567890
    LinkedIn: https://linkedin.com/in/johndoe
    
    Summary:
    Experienced software engineer with 5 years of experience in Python development.
    
    Skills:
    - Python, Django, Flask
    - JavaScript, React
    - Docker, Kubernetes
    - AWS, GCP
    
    Experience:
    Software Engineer at Tech Corp (2018-Present)
    - Developed and maintained web applications
    - Led a team of 3 developers
    
    Education:
    Bachelor of Computer Science, University of Technology (2014-2018)
    """


@pytest.fixture
def sample_jd_text():
    """Sample job description text for testing."""
    return """
    Senior Python Developer
    
    About the Role:
    We are looking for a Senior Python Developer with experience in web frameworks.
    
    Requirements:
    - 5+ years of experience in Python development
    - Experience with Django or Flask
    - Knowledge of frontend technologies (JavaScript, React)
    - Experience with containerization (Docker, Kubernetes)
    - Cloud platform experience (AWS, GCP, or Azure)
    
    Responsibilities:
    - Develop and maintain web applications
    - Lead a team of developers
    - Collaborate with product managers and designers
    """


@pytest.fixture
def mock_gemini_client():
    """Mock Gemini client for testing."""
    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock()
    return mock_client


@pytest.fixture
def mock_notion_manager():
    """Mock Notion manager for testing."""
    mock_manager = AsyncMock()
    mock_manager.check_for_duplicate = AsyncMock(return_value=False)
    mock_manager.create_candidate_row = AsyncMock(return_value="test_page_id")
    mock_manager.configure = AsyncMock(return_value=mock_manager)
    return mock_manager


@pytest.fixture
def mock_console():
    """Mock Rich console for testing."""
    mock_console = MagicMock(spec=Console)
    # Add required attributes for Rich Progress
    mock_console.get_time = MagicMock(return_value=time.monotonic())
    mock_console.is_jupyter = False
    mock_console.is_interactive = True
    return mock_console

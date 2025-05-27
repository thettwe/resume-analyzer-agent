"""
Tests for Notion integration
"""

import os
import sys
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from rich.console import Console

# Add src directory to path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from api.models import Candidate
from api.notion import NotionManager
from core.notion_upload import upload_to_notion


class TestNotionIntegration:
    """Tests for Notion integration."""

    @pytest.fixture
    def sample_candidate(self):
        """Create a sample candidate for testing."""
        return Candidate(
            full_name="John Doe",
            email="john.doe@example.com",
            contact_number="+1234567890",
            date_of_birth="1990-01-01",
            gender="Male",
            linkedin_url="https://linkedin.com/in/johndoe",
            years_of_experience=5,
            experience_summary="5 years of Python development experience",
            profile_summary="Experienced software engineer with 5 years of experience in Python development.",
            professional_skills=["Python", "Django", "React"],
            personal_skills=["Problem solving", "Communication"],
            match_score=88,
            ranking_category="High Fit",
            ranking_reason="The candidate has the required skills and experience for the role.",
            job_location="Singapore",
            job_position_title="Senior Python Developer",
        )

    @pytest.mark.asyncio
    async def test_notion_manager_initialization(self):
        """Test NotionManager initialization with timezone."""
        # Create a mock client to prevent actual API calls
        mock_client = AsyncMock()

        # Mock the NotionClient constructor
        with patch("api.notion.NotionClient", return_value=mock_client):
            # Initialize NotionManager with timezone
            manager = NotionManager(
                token="test_token", database_id="test_db", timezone="Europe/Berlin"
            )

            # Check if timezone was stored correctly - the timezone is converted to a timezone object
            # so we check the timezone name instead of string equality
            assert manager.timezone.zone == "Europe/Berlin"

            # Configure the manager
            configured_manager = await manager.configure()

            # Verify client was created and methods were called
            assert manager.client == mock_client
            mock_client.users.me.assert_called_once()
            mock_client.databases.retrieve.assert_called_once_with(
                database_id="test_db"
            )

            # Verify manager is returned for chaining
            assert configured_manager == manager

    @pytest.mark.asyncio
    async def test_upload_to_notion(
        self, mock_notion_manager, mock_console, sample_candidate
    ):
        """Test uploading candidates to Notion."""
        # Create mock candidates
        candidates = [
            {
                "status": "success",
                "file_name": "cv1.pdf",
                "file_path": "path/to/cv1.pdf",
                "candidate": sample_candidate,
            },
            {
                "status": "success",
                "file_name": "cv2.pdf",
                "file_path": "path/to/cv2.pdf",
                "candidate": sample_candidate,
            },
        ]

        # Call the function
        successful, duplicate, failed = await upload_to_notion(
            candidates=candidates,
            notion_manager=mock_notion_manager,
            console=mock_console,
            max_concurrent=2,
        )

        # Verify result
        assert successful == 2
        assert duplicate == 0
        assert failed == 0

        # Verify calls to the notion manager
        assert mock_notion_manager.check_for_duplicate.call_count == 2
        assert mock_notion_manager.create_candidate_row.call_count == 2

    @pytest.mark.asyncio
    async def test_upload_to_notion_with_duplicate(
        self, mock_notion_manager, mock_console, sample_candidate
    ):
        """Test uploading candidates to Notion with duplicates."""
        # Setup mocks
        mock_console = MagicMock(spec=Console)
        # Add required attributes for Rich Progress
        mock_console.get_time = MagicMock(return_value=time.monotonic())
        mock_console.is_jupyter = False
        mock_console.is_interactive = True

        mock_notion_manager.check_for_duplicate.side_effect = [True, False]

        # Create mock candidates
        candidates = [
            {
                "status": "success",
                "file_name": "cv1.pdf",
                "file_path": "path/to/cv1.pdf",
                "candidate": sample_candidate,
            },
        ]

        # Call the function
        successful, duplicate, failed = await upload_to_notion(
            candidates=candidates,
            notion_manager=mock_notion_manager,
            console=mock_console,
            max_concurrent=2,
        )

        # Verify result
        assert successful == 0
        assert duplicate == 1
        assert failed == 0

        # Verify calls to the notion manager
        assert mock_notion_manager.check_for_duplicate.call_count == 1
        assert mock_notion_manager.create_candidate_row.call_count == 0

    @pytest.mark.asyncio
    async def test_upload_to_notion_with_failure(
        self, mock_notion_manager, mock_console, sample_candidate
    ):
        """Test uploading candidates to Notion with failures."""
        # Setup mocks
        mock_console = MagicMock(spec=Console)
        # Add required attributes for Rich Progress
        mock_console.get_time = MagicMock(return_value=time.monotonic())
        mock_console.is_jupyter = False
        mock_console.is_interactive = True

        mock_notion_manager.check_for_duplicate.return_value = False
        mock_notion_manager.create_candidate_row.side_effect = [None, "page_id"]

        # Create mock candidates
        candidates = [
            {
                "status": "success",
                "file_name": "cv1.pdf",
                "file_path": "path/to/cv1.pdf",
                "candidate": sample_candidate,
            },
        ]

        # Call the function
        successful, duplicate, failed = await upload_to_notion(
            candidates=candidates,
            notion_manager=mock_notion_manager,
            console=mock_console,
            max_concurrent=2,
        )

        # Verify result
        assert successful == 0
        assert duplicate == 0
        assert failed == 1

        # Verify calls to the notion manager
        assert mock_notion_manager.check_for_duplicate.call_count == 1
        assert mock_notion_manager.create_candidate_row.call_count == 1

    @pytest.mark.asyncio
    async def test_upload_to_notion_with_api_exception(
        self, mock_notion_manager, mock_console, sample_candidate
    ):
        """Test upload_to_notion function with an API exception."""
        # Configure mock to raise an exception
        mock_notion_manager.check_for_duplicate = AsyncMock(
            side_effect=Exception("API error")
        )

        # Sample candidates data
        candidates = [
            {
                "status": "success",
                "file_name": "cv1.pdf",
                "file_path": "path/to/cv1.pdf",
                "candidate": sample_candidate,
            },
        ]

        # Execute
        successful, duplicate, failed = await upload_to_notion(
            candidates=candidates,
            notion_manager=mock_notion_manager,
            console=mock_console,
            max_concurrent=2,
        )

        # Assert
        assert successful == 0
        assert duplicate == 0
        assert failed == 1

        # Verify Notion API calls
        mock_notion_manager.check_for_duplicate.assert_called_once()
        mock_notion_manager.create_candidate_row.assert_not_called()

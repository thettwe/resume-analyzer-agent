"""
Tests for Gemini API integration
"""

import os
import sys
from unittest.mock import MagicMock

import pytest
from google.genai import types

# Add src directory to path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from api.gemini import get_candidate_info
from api.models import Candidate
from core.gemini_processing import process_with_gemini


class TestGeminiAPI:
    """Tests for Gemini API integration."""

    sample_candidate_json = {
        "full_name": "John Doe",
        "email": "john.doe@example.com",
        "contact_number": "+1234567890",
        "date_of_birth": "1990-01-01",
        "gender": "Male",
        "linkedin_url": "https://linkedin.com/in/johndoe",
        "years_of_experience": 5,
        "experience_summary": "5 years of Python development experience",
        "profile_summary": "Experienced software engineer",
        "professional_skills": ["Python", "Django", "React"],
        "personal_skills": ["Problem solving", "Communication"],
        "match_score": 88,
        "ranking_category": "High Fit",
        "ranking_reason": "Strong match for requirements",
        "job_location": "Singapore",
        "job_position_title": "Senior Python Developer",
    }

    @pytest.mark.asyncio
    async def test_get_candidate_info(
        self, mock_gemini_client, sample_cv_text, sample_jd_text
    ):
        """Test get_candidate_info function."""
        # Create a candidate instance from the sample data
        candidate = Candidate(**self.sample_candidate_json)

        # Setup mock response
        mock_response = MagicMock(spec=types.GenerateContentResponse)
        mock_response.text = self.sample_candidate_json
        mock_response.parsed = candidate
        mock_gemini_client.aio.models.generate_content.return_value = mock_response

        # Execute
        result = await get_candidate_info(
            cv_text=sample_cv_text,
            jd_text=sample_jd_text,
            client=mock_gemini_client,
            model="gemini-2.0-flash",
            temperature=0.0,
        )

        # Assert
        assert isinstance(result, Candidate)
        assert result.full_name == "John Doe"
        assert result.email == "john.doe@example.com"
        assert result.match_score == 88

    @pytest.mark.asyncio
    async def test_process_with_gemini(
        self, mock_gemini_client, sample_jd_text, mock_console
    ):
        """Test process_with_gemini function."""
        # Create a candidate instance from the sample data
        candidate = Candidate(**self.sample_candidate_json)

        # Setup mock response
        mock_response = MagicMock(spec=types.GenerateContentResponse)
        mock_response.text = self.sample_candidate_json
        mock_response.parsed = candidate
        mock_gemini_client.aio.models.generate_content.return_value = mock_response

        # Sample CV data
        cv_data = [
            {
                "file_name": "cv1.pdf",
                "file_path": "path/to/cv1.pdf",
                "text": "CV1 content",
            },
            {
                "file_name": "cv2.pdf",
                "file_path": "path/to/cv2.pdf",
                "text": "CV2 content",
            },
        ]

        # Execute
        results = await process_with_gemini(
            cv_data=cv_data,
            jd_text=sample_jd_text,
            gemini_client=mock_gemini_client,
            model="gemini-2.0-flash",
            temperature=0.0,
            console=mock_console,
            max_concurrent=2,
        )

        # Assert
        assert len(results) == 2
        for result in results:
            assert isinstance(result, dict)
            assert "status" in result
            assert "candidate" in result
            assert isinstance(result["candidate"], Candidate)
            assert result["candidate"].full_name == "John Doe"
            assert result["candidate"].match_score == 88

    @pytest.mark.asyncio
    async def test_process_with_gemini_error(
        self, mock_gemini_client, sample_jd_text, mock_console
    ):
        """Test process_with_gemini function with an error."""
        # Setup mock to raise an exception
        mock_gemini_client.aio.models.generate_content.side_effect = Exception(
            "API error"
        )

        # Sample CV data
        cv_data = [
            {
                "file_name": "cv1.pdf",
                "file_path": "path/to/cv1.pdf",
                "text": "CV1 content",
            },
        ]

        # Execute
        result = await process_with_gemini(
            cv_data=cv_data,
            jd_text=sample_jd_text,
            gemini_client=mock_gemini_client,
            model="gemini-2.0-flash",
            temperature=0.0,
            console=mock_console,
            max_concurrent=2,
        )

        # Assert that no results were processed successfully
        assert len(result) == 0

        # Verify API call was attempted
        mock_gemini_client.aio.models.generate_content.assert_called_once()

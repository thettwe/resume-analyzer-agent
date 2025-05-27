"""
Tests for data models
"""

import os
import sys

import pytest
from pydantic import ValidationError

# Add src directory to path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from api.models import Candidate


class TestModels:
    """Tests for data models."""

    def test_candidate_valid_data(self):
        """Test creating a Candidate with valid data."""
        data = {
            "full_name": "John Doe",
            "email": "john@example.com",
            "contact_number": "+1234567890",
            "linkedin_url": "https://linkedin.com/in/johndoe",
            "gender": "Male",
            "date_of_birth": "1990-01-01",
            "years_of_experience": 5,
            "personal_skills": ["Communication", "Leadership"],
            "professional_skills": ["Python", "JavaScript"],
            "experience_summary": "5 years of software development experience",
            "match_score": 85,
            "ranking_category": "High Fit",
            "ranking_reason": "Strong technical skills and experience",
            "job_location": "Singapore",
            "job_position_title": "Senior Software Engineer",
        }

        candidate = Candidate(**data)
        assert candidate.full_name == "John Doe"
        assert candidate.email == "john@example.com"
        assert candidate.years_of_experience == 5
        assert len(candidate.professional_skills) == 2
        assert len(candidate.personal_skills) == 2
        assert candidate.match_score == 85
        assert candidate.ranking_category == "High Fit"

    def test_candidate_missing_required_field(self):
        """Test creating a Candidate with missing required field."""
        data = {
            "full_name": "John Doe",
            # email is missing
            "contact_number": "+1234567890",
            "linkedin_url": "https://linkedin.com/in/johndoe",
            "gender": "Male",
            "date_of_birth": "1990-01-01",
            "years_of_experience": 5,
            "personal_skills": ["Communication", "Leadership"],
            "professional_skills": ["Python", "JavaScript"],
            "experience_summary": "5 years of software development experience",
            "match_score": 85,
            "ranking_category": "High Fit",
            "ranking_reason": "Strong technical skills and experience",
            "job_location": "Singapore",
            "job_position_title": "Senior Software Engineer",
        }

        with pytest.raises(ValidationError) as excinfo:
            Candidate(**data)
        assert "email" in str(excinfo.value)

    def test_candidate_invalid_gender(self):
        """Test creating a Candidate with invalid gender."""
        data = {
            "full_name": "John Doe",
            "email": "john@example.com",
            "contact_number": "+1234567890",
            "linkedin_url": "https://linkedin.com/in/johndoe",
            "gender": "Invalid",  # Invalid gender value
            "date_of_birth": "1990-01-01",
            "years_of_experience": 5,
            "personal_skills": ["Communication", "Leadership"],
            "professional_skills": ["Python", "JavaScript"],
            "experience_summary": "5 years of software development experience",
            "match_score": 85,
            "ranking_category": "High Fit",
            "ranking_reason": "Strong technical skills and experience",
            "job_location": "Singapore",
            "job_position_title": "Senior Software Engineer",
        }

        with pytest.raises(ValidationError) as excinfo:
            Candidate(**data)
        assert "gender" in str(excinfo.value)

    def test_candidate_invalid_ranking_category(self):
        """Test creating a Candidate with invalid ranking category."""
        data = {
            "full_name": "John Doe",
            "email": "john@example.com",
            "contact_number": "+1234567890",
            "linkedin_url": "https://linkedin.com/in/johndoe",
            "gender": "Male",
            "date_of_birth": "1990-01-01",
            "years_of_experience": 5,
            "personal_skills": ["Communication", "Leadership"],
            "professional_skills": ["Python", "JavaScript"],
            "experience_summary": "5 years of software development experience",
            "match_score": 85,
            "ranking_category": "Invalid",  # Invalid ranking category
            "ranking_reason": "Strong technical skills and experience",
            "job_location": "Singapore",
            "job_position_title": "Senior Software Engineer",
        }

        with pytest.raises(ValidationError) as excinfo:
            Candidate(**data)
        assert "ranking_category" in str(excinfo.value)

    def test_candidate_invalid_match_score(self):
        """Test creating a Candidate with invalid match score."""
        data = {
            "full_name": "John Doe",
            "email": "john@example.com",
            "contact_number": "+1234567890",
            "linkedin_url": "https://linkedin.com/in/johndoe",
            "gender": "Male",
            "date_of_birth": "1990-01-01",
            "years_of_experience": 5,
            "personal_skills": ["Communication", "Leadership"],
            "professional_skills": ["Python", "JavaScript"],
            "experience_summary": "5 years of software development experience",
            "match_score": -1,  # Invalid match score
            "ranking_category": "High Fit",
            "ranking_reason": "Strong technical skills and experience",
            "job_location": "Singapore",
            "job_position_title": "Senior Software Engineer",
        }

        with pytest.raises(ValidationError) as excinfo:
            Candidate(**data)
        assert "match_score" in str(excinfo.value)

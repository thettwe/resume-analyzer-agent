"""
Data models for the application.
"""

from typing import List, Literal

from pydantic import BaseModel, Field


class Candidate(BaseModel):
    """Represents a candidate's profile."""

    full_name: str
    email: str
    contact_number: str
    linkedin_url: str
    gender: Literal["Male", "Female", "N/A"]
    date_of_birth: str
    years_of_experience: int = Field(ge=0)
    personal_skills: List[str]
    professional_skills: List[str]
    experience_summary: str
    match_score: int = Field(ge=0, le=100)
    ranking_category: Literal["No Fit", "High Fit", "Medium Fit", "Low Fit"]
    ranking_reason: str
    job_location: str
    job_position_title: str

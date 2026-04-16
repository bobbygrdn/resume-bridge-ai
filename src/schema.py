from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
from datetime import date

# MatchAnalysis Class to represent the analysis of how well a resume matches a job description
class MatchAnalysis(BaseModel):
    match_score: int = Field(ge=0, le=100, description="Probability of fit for this role")
    key_alignments: List[str] = Field(description="Specific points where the resume matches job needs")
    skill_gaps: List[str] = Field(description="Skills or experience missing for this role")
    personalized_pitch: str = Field(description="A customized 1-paragraph summary for an application")

# JobInquiry Class to represent the API request body for analyzing a resume against a job description
class JobInquiry(BaseModel):
    target_url: str
    user_id: str = "default_user"
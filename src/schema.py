from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
from datetime import date

# Certifications Class to represent professional certifications in the resume
class Certification(BaseModel):
    name: str = Field(description="The name of the certification or badge")
    issuing_organization: str = Field(description="e.g., AWS, Microsoft, Coursera")
    issue_date: Optional[str] = None
    credential_id: Optional[str] = None
    credential_url: Optional[HttpUrl] = None

# Experience Class to represent work experience in the resume
class Experience(BaseModel):
    company: str
    role: str
    start_date: date
    end_date: Optional[str] = "Present"
    description: List[str] = Field(description="Bullet points of key responsibilities and achievements")

# Education Class to represent educational background in the resume
class Education(BaseModel):
    institution: str
    degree: str
    graduation_year: int

# ResumeProfile Class to represent the overall resume profile
class ResumeProfile(BaseModel):
    full_name: str
    headline: str = Field(max_length=60, description="A short professional tagline (e.g., 'Senior AI Engineer')")
    email: str
    github_url: Optional[HttpUrl] = None
    portfolio_url: Optional[HttpUrl] = None
    summary: str = Field(description="A 2-3 sentence professional summary")
    target_roles: List[str] = Field(description="Specific job titles or niches the user is pursuing (e.g., 'AI Engineer', 'Backend Developer')")
    skills: List[str] = Field(description="Core technical and soft skills")
    certifications: List[Certification] = Field(default_factory=list)
    experience: List[Experience]
    education: List[Education]

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

# JobPosting Class to represent the structured data extracted from a job posting
class JobPosting(BaseModel):
    company_name: str
    job_title: str
    location: str = Field(description="City, State, or 'Remote'")
    tech_stack: List[str] = Field(description="List of required languages, frameworks, or tools")
    requirements: List[str] = Field(description="Core responsibilities or must-have experience")
    is_technical: bool = Field(description="Whether this is a software, AI, or data role")
    salary_range: Optional[str] = "Not Listed"
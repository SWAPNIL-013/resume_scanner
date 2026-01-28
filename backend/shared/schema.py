from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import List,Dict,Any, Optional

class Project(BaseModel):
    title: str
    description: str
    technologies: List[str]

class Education(BaseModel):
    degree: str
    institution: str
    year: str

class Experience(BaseModel):
    company: str
    role: Optional[str] = None
    start_date: Optional[str]=None
    end_date: Optional[str]=None
    description: Optional[str]=None
    duration_years: Optional[str] = None


class ResumeSchema(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None 
    phone: Optional[str] = None
    location: Optional[str]=None
    urls: List[str] = []
    skills: List[str] = []
    projects: List[Project] = []
    education: List[Education] = []
    experience: List[Experience] = []
    certifications: List[str] = []
  
class ExportRequest(BaseModel):
    processed_resumes: List[Dict]
    mode: str = "new_file"           
    file_path: Optional[str] = None  
    sheet_name: Optional[str] = None  

class RegisterRequest(BaseModel):
    username: str
    password: str
    full_name: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str

class JobDescriptionSchema(BaseModel):
    """
    Dynamic Job Description schema that can handle variable JD fields.
    Example:
    {
        "title": "Data Scientist",
        "skills": ["Python", "ML"],
        "experience": "2+ years",
        "location": "pune",
        "tools": ["TensorFlow", "SQL"]
    }
    """
    title: Optional[str] = None
    fields: Dict[str, Any] = Field(default_factory=dict)  # dynamic fields

    class Config:
        extra = "allow"  # allow additional dynamic keys



class Evaluation(BaseModel):
    jd_id: str
    jd_title: str
    score: float
    overall_summary: List[str] = []
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    other_skills: List[str] = []
    scoring_breakdown: dict = {}
    evaluated_at: Optional[datetime] = None

class ResumeInfo(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    urls: List[str] = []
    skills: List[str] = []
    projects: List[Project] = []
    education: List[Education] = []
    experience: List[Experience] = []
    certifications: List[str] = []
    total_experience_years: Optional[str] = None
    uploaded_at: Optional[datetime] = None

# used by db_fetcher
class ResumeDBSchema(BaseModel):
    _id: Optional[str]
    resume_json: ResumeInfo
    evaluations: List[Evaluation] = []


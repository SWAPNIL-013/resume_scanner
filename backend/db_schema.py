from pydantic import BaseModel
from typing import List, Optional

class Project(BaseModel):
    title: str
    description: str
    technologies: List[str] = []

class Education(BaseModel):
    degree: str
    institution: str
    year: str

class Experience(BaseModel):
    company: str
    role: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: str
    duration_years: Optional[str] = None

class ResumeDBSchema(BaseModel):
    _id: Optional[str]
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
    uploaded_at: Optional[str] = None

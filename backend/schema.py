from token import OP
from pydantic import BaseModel, EmailStr
from typing import List,Dict, Optional

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
    start_date: str
    end_date: str
    description: str
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
    mode: str = "new_file"            # "new_file", "append_sheet", "new_sheet"
    file_path: Optional[str] = None   # Existing file path if append/new_sheet
    sheet_name: Optional[str] = None  # Name of sheet to append/create

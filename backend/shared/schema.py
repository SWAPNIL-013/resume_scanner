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



# db_schema
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

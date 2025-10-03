from pydantic import BaseModel
from typing import List,Dict, Optional

class JobDescriptionSchema(BaseModel):
    title: str
    skills: List[str]
    education: Optional[str]=None
    experience: Optional[str]=None
    responsibilities: Optional[List[str]]=None
    certifications: Optional[List[str]] = None
    
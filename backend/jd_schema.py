    
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional

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

# jd_llm.py
import os
import json
from dotenv import load_dotenv
from google import genai
from jd_schema import JobDescriptionSchema
from utils import call_llm

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def generate_jd_json(jd_text: str, *, api_key: str = None, model: str = "gemini-2.5-flash") -> dict:
    """
    Convert JD text into structured JSON using LLM.
    """
    prompt = f"""
    You are a JD parser. Extract all relevant fields from the following JD and output JSON ONLY
    matching this schema:
    
    {{
        "title": "string",
        "skills": ["list of required skills"],
        "education": "optional string",
        "experience": "optional string",
        "responsibilities": ["optional list of responsibilities"],
        "certifications": ["optional list of certifications"]
    }}
    
    JD Text:
    {jd_text}
    """
    
    # Use centralized LLM caller (benefits from retries and structured errors)
    llm_result = call_llm(prompt, model=model, api_key=api_key)

    if isinstance(llm_result, dict) and llm_result.get("error"):
        print(f"JD parsing failed: {llm_result.get('error')}")
        return {}

    # llm_result should be a dict (parsed JSON) or a raw string
    if isinstance(llm_result, dict):
        parsed = llm_result
    else:
        try:
            parsed = json.loads(llm_result)
        except json.JSONDecodeError:
            print("JD parsing failed: LLM returned non-JSON response")
            return {}

    try:
        jd = JobDescriptionSchema.model_validate(parsed)
        return jd.model_dump()
    except Exception as e:
        print(f"JD schema validation failed: {e}")
        return {}


# ---- Test Code -------
if __name__ == "__main__":
    sample_jd = """
    Job Title: Data Scientist
    Skills: Python, SQL, Machine Learning, Deep Learning
    Education: B.Tech in Computer Science or equivalent
    Experience: 2-4 years
    Responsibilities:
    - Build ML models
    - Analyze data and generate insights
    - Collaborate with cross-functional teams
    Certifications: AWS Certified Machine Learning
    """

    jd_json = generate_jd_json(sample_jd)
    print("Parsed JD JSON:")
    print(json.dumps(jd_json, indent=2))

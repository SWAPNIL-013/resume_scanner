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
    Dynamically extract fields from a Job Description text using LLM.
    Output: Flexible JSON with title + any relevant attributes (skills, experience, etc.)
    """
    prompt = f"""
    You are an intelligent JD parser. Extract ALL relevant and meaningful fields from the given job description. 
    Always return a valid JSON object.

    Example structure (but it can vary dynamically):
    {{
        "title": "Data Scientist",
        "skills": ["Python", "SQL", "ML"],
        "education": "Bachelor's in Computer Science",
        "experience": "2-4 years",
        "responsibilities": ["Build ML models", "Analyze data"],
        "certifications": ["AWS ML Foundations"],
        "tools": ["TensorFlow", "PowerBI"]
    }}

    Guidelines:
    - Keep keys concise and descriptive (e.g., skills, education, tools, domain, etc.).
    - Include only fields relevant to job qualifications.
    - Ensure pure JSON, no markdown, no commentary.

    Job Description Text:
    {jd_text}
    """

    # ✅ Use centralized LLM caller (handles retries & errors)
    llm_result = call_llm(prompt, model=model, api_key=api_key)

    if isinstance(llm_result, dict) and llm_result.get("error"):
        print(f"JD parsing failed: {llm_result.get('error')}")
        return {}

    # ✅ Parse JSON safely
    if isinstance(llm_result, dict):
        parsed = llm_result
    else:
        try:
            parsed = json.loads(llm_result)
        except json.JSONDecodeError:
            print("JD parsing failed: LLM returned non-JSON response")
            return {}

    # ✅ Normalize: title separate, rest dynamic
    title = parsed.get("title", None)
    fields = {k: v for k, v in parsed.items() if k.lower() != "title"}

    try:
        jd = JobDescriptionSchema(title=title, fields=fields)
        return jd.model_dump()
    except Exception as e:
        print(f"JD schema validation failed: {e}")
        return {"title": title, "fields": fields}


# ---- Local Test -------
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
    Tools: TensorFlow, PowerBI
    """
    jd_json = generate_jd_json(sample_jd)
    print("Parsed JD JSON:")
    print(json.dumps(jd_json, indent=2))

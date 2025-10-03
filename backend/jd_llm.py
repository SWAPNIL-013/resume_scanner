# jd_llm.py
import os
import json
from dotenv import load_dotenv
from google import genai
from jd_schema import JobDescriptionSchema

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def generate_jd_json(jd_text: str) -> dict:
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
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[{"parts":[{"text": prompt}]}]
        )

        raw_output = response.text.strip()

        # Remove markdown if present
        if raw_output.startswith("```json"):
            raw_output = raw_output[len("```json"):].strip()
        if raw_output.startswith("```"):
            raw_output = raw_output[len("```"):].strip()
        if raw_output.endswith("```"):
            raw_output = raw_output[:-len("```")].strip()

        parsed = json.loads(raw_output)
        jd = JobDescriptionSchema.model_validate(parsed)
        return jd.model_dump()
    
    except Exception as e:
        print(f"JD parsing failed: {e}")
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

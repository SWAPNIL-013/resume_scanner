# scoring_llm.py
import json
from utils import call_llm

def generate_score(resume_json: dict, jd_json: dict, weights: dict, resume_total_experience: float, *, api_key: str = None, model: str = "gemini-2.5-flash") -> dict:
    """
    Use LLM to score a resume against the job description.
    Also returns matched_skills and other_skills based on semantic similarity.
    """
    prompt = f"""
You are a resume scoring assistant. Compare the resume JSON and job description JSON below.

Resume JSON:
{json.dumps(resume_json, indent=2)}

JD JSON:
{json.dumps(jd_json, indent=2)}

The candidate has {resume_total_experience:.2f} years of experience.

The weights are:
{json.dumps(weights, indent=2)}

Instructions:
1. Score each category (skills, experience, education, certifications) from 0–100.
   - Skills, education, and certifications scoring should be based on overlap/match quality.
   - Experience score must be calculated as:
       if candidate_exp >= jd_exp → 100
       else → (candidate_exp / jd_exp) * 100 (rounded to 2 decimals).
   - If JD does not specify required experience, score experience relatively based on resume strength.
2. For the total score, compute as:  
   total = (skills_score * weights['skills'] + 
            experience_score * weights['experience'] + 
            education_score * weights['education'] + 
            certifications_score * weights['certifications'])
   Return total rounded to 2 decimal places.
3. For experience, if resume experience is less than JD requirement, add a remark: 
   "Experience is below required X years", replacing X with required years.
4. Include other remarks for gaps or strengths in skills, education, or certifications.
5. Also, classify the resume skills into:
   - "matched_skills": skills from the resume that semantically match the JD skills
   - "missing_skills": skills from JD that does not semantically match with resume skills
   - "other_skills": remaining skills from the resume
6. Return strictly in JSON format as:

{{
  "skills": <float>,
  "experience": <float>,
  "education": <float>,
  "certifications": <float>,
  "total": <float>,
  "remarks": ["list of strings"],
  "matched_skills": ["list of matched skills"],
  "missing_skills": ["list of unmatched/missing skills"],
  "other_skills": ["list of other skills"]
}}
"""

    # Call your LLM function
    result = call_llm(prompt, model=model, api_key=api_key)

    # If LLM returned an error structure, return a safe default scoring object
    if isinstance(result, dict) and result.get("error"):
        err = result.get("error")
        print(f"[LLM ERROR] {err}")
        # Safe default scoring structure
        return {
            "skills": 0.0,
            "experience": 0.0,
            "education": 0.0,
            "certifications": 0.0,
            "total": 0.0,
            "remarks": [f"LLM error: {err.get('message') or str(err)}"],
            "matched_skills": [],
            "missing_skills": [],
            "other_skills": []
        }

    return result


# ----------------- Test Runner -----------------
if __name__ == "__main__":
    # dummy data for quick test
    resume_json = {
        "skills": ["Python", "SQL","ML"],
        "experience": [
            {"company": "X", "role": "Dev", "start_date": "2022-01", "end_date": "2023-01"}
        ],
        "education": [{"degree": "B.Tech", "institution": "ABC University", "year": "2022"}],
        "certifications": ["AWS Certified"]
    }

    jd_json = {
        "skills": ["Python", "Machine Learning","Tableau"],
        "experience": "2 yr",
        "education": "B.Tech",
        "certifications": ["AWS Certified", "Azure Certified"]
    }

    weights = {"skills": 0.4, "experience": 0.3, "education": 0.2, "certifications": 0.1}

    # Example: calculated total experience from utils
    resume_total_experience = 2.0  # in years
    print("Evaluating...")
    result = generate_score(resume_json, jd_json, weights, resume_total_experience)
    print(json.dumps(result, indent=2))

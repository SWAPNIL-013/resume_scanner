import json
from utils import call_llm


def generate_score(
    resume_json: dict,
    jd_json: dict,
    weights: dict,
    resume_total_experience: float,
    *,
    api_key: str = None,
    model: str = "gemini-2.5-flash"
) -> dict:
    """
    Use LLM to score a resume against a dynamically structured job description.
    Returns both per-field and total scores with remarks and skill matching.
    """

    # ---- Extract JD fields dynamically ----
    jd_fields = jd_json.get("fields", jd_json)  # fallback if older JD format
    field_list = list(jd_fields.keys())

    # ---- Dynamic scoring instructions ----
    field_scoring_instructions = "\n".join(
        [f"- {field}: score this category from 0–100 based on semantic match quality." for field in field_list]
    )

    # ---- Total Score formula (LLM can decide dynamically) ----
    prompt = f"""
You are a resume scoring assistant. Compare the following resume JSON with the job description JSON.

Resume JSON:
{json.dumps(resume_json, indent=2)}

JD JSON:
{json.dumps(jd_json, indent=2)}

The candidate has {resume_total_experience:.2f} years of experience.

The available fields are:
{json.dumps(field_list, indent=2)}

Weights:
{json.dumps(weights, indent=2)}

Instructions:
1. Evaluate each field listed above.
{field_scoring_instructions}

2. If a field like "experience" contains years, score it as:
   - If candidate_exp >= jd_exp → 100
   - Else → (candidate_exp / jd_exp) * 100 (rounded to 2 decimals).
   - If JD has no experience requirement, estimate relative to resume content.

3. Compute total score as the weighted sum of all available field scores.
   Example:
   total = Σ(field_score[field] × weights[field])
   Return total rounded to 2 decimals.

4. Add "remarks" for any missing qualifications or outstanding strengths.

5. Additionally classify skills into:
   - "matched_skills": resume skills that match JD skills
   - "missing_skills": JD skills not found in resume
   - "other_skills": remaining resume skills

Return strictly in JSON format as:
{{
  "field_scores": {{
     "skills": <float>,
     "experience": <float>,
     "education": <float>,
     ...
  }},
  "total": <float>,
  "remarks": ["list of strings"],
  "matched_skills": ["list"],
  "missing_skills": ["list"],
  "other_skills": ["list"]
}}
"""

    # ---- Call LLM ----
    result = call_llm(prompt, model=model, api_key=api_key)

    # ---- Handle LLM error ----
    if isinstance(result, dict) and result.get("error"):
        err = result["error"]
        print(f"[LLM ERROR] {err}")
        # Create a fallback structure for safe return
        return {
            "field_scores": {field: 0.0 for field in field_list},
            "total": 0.0,
            "remarks": [f"LLM error: {err.get('message', str(err))}"],
            "matched_skills": [],
            "missing_skills": [],
            "other_skills": []
        }

    return result


# ----------------- Test Runner -----------------
if __name__ == "__main__":
    resume_json = {
        "skills": ["Python", "SQL", "ML"],
        "experience": [
            {"company": "X", "role": "Dev", "start_date": "2022-01", "end_date": "2023-01"}
        ],
        "education": [{"degree": "B.Tech", "institution": "ABC University", "year": "2022"}],
        "certifications": ["AWS Certified"]
    }

    jd_json = {
        "title": "Data Scientist",
        "fields": {
            "skills": ["Python", "Machine Learning", "Tableau"],
            "experience": "2 yr",
            "education": "B.Tech",
            "certifications": ["AWS Certified", "Azure Certified"],
            "tools": ["TensorFlow", "PowerBI"]
        }
    }

    weights = {
        "skills": 0.3,
        "experience": 0.25,
        "education": 0.2,
        "certifications": 0.15,
        "tools": 0.1
    }

    resume_total_experience = 2.0
    print("Evaluating...\n")
    result = generate_score(resume_json, jd_json, weights, resume_total_experience)
    print(json.dumps(result, indent=2))

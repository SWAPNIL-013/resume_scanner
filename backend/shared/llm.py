import json
from typing import Dict
from pydantic import ValidationError
from backend.shared.schema import ResumeSchema,JobDescriptionSchema
from backend.shared.utils import add_experience_duration_readable, call_llm, compute_total_score

# ----------------- Generate Resume JSON -----------------
def generate_resume_json(text: str, *, api_key: str = None, model: str = "gemini-2.5-flash") -> Dict:
    prompt = f"""
    You are a resume parser. Extract the following fields from the text and return JSON ONLY.

    Rules:
    - Only include professional work experience or internships in "experience".
    - Do NOT include hackathons, competitions, volunteering, or extracurricular activities in "experience".
    - If start_date or end_date are missing, set them as empty strings "".
    - For "urls", include only professional profile or project links (LinkedIn, GitHub, portfolio, project demos). Do NOT include email (mailto:) or phone (tel:) links.
    - Extract the candidate's **current location** (city, state, or country) only if it is mentioned in the "About Me", "Contact", or introductory summary sections.
    - Do NOT include locations from education, work experience, projects, or certifications.
    - If no location is mentioned in these sections, set location as an empty string "".


    Output JSON schema:

    {{
        "name": "string",
        "email": "string",
        "phone": "string",
        "location": "string",
        "urls": ["list of professional profile or project links"],
        "skills": ["list of skills"],
        "projects": [
            {{"title": "string","description": "string","technologies": ["list of technologies"]}}
        ],
        "education": [
            {{"degree": "string","institution": "string","year": "string"}}
        ],
        "experience": [
            {{"company": "string","role": "string","start_date": "YYYY-MM or empty string","end_date": "YYYY-MM, Present, or empty string"}}
        ],
        "certifications": ["list of certifications"]
    }}

    Resume text:
    {text}
    """

    # Call LLM
    llm_output = call_llm(prompt, model=model, api_key=api_key)

    # ----------------- Handle LLM errors -----------------
    if isinstance(llm_output, dict) and llm_output.get("error"):
        err = llm_output.get("error")
        print(f"[LLM ERROR] {err}")
        # Return an empty validated resume schema so downstream code has consistent shape
        parsed_json = {}
    else:
        # llm_output might already be a dict (parsed JSON) or a raw string
        if isinstance(llm_output, dict):
            parsed_json = llm_output
        else:
            try:
                parsed_json = json.loads(llm_output)
            except json.JSONDecodeError:
                print("⚠️ LLM output is not valid JSON. Returning empty resume structure.")
                parsed_json = {}

    # ----------------- Validate and enrich -----------------
    try:
        resume = ResumeSchema.model_validate(parsed_json)
        resume_dict = resume.model_dump()
    except ValidationError as e:
        print(f"⚠️ Validation error: {e}")
        resume_dict = ResumeSchema().model_dump()  # return empty default schema

    # Add human-readable experience duration
    resume_dict = add_experience_duration_readable(resume_dict)

    return resume_dict


# # ----------------- Test Runner -----------------
# if __name__ == "__main__":
#     import json
#     from parser import extract_text_and_links  # your parser
#     from shared.utils import total_experience_from_resume

#     resume_file = "samples/Naukri_Mr.IMRANSHARIFFHS[3y_8m].pdf"

#     # Extract text + links
#     resume_text, resume_links = extract_text_and_links(resume_file)

#     print("----- Extracted Resume Text (first 500 chars) -----")
#     print(resume_text[:500])

#     print("\n----- Extracted Links -----")
#     if resume_links:
#         for link in resume_links:
#             print(link)
#     else:
#         print("No links found")

#     print("\n------- Running LLM to extract structured JSON ----------")
#     resume_text_with_links = resume_text + "\n\nLinks found: " + ", ".join(resume_links)

#     # Run LLM parser
#     resume_dict = generate_resume_json(resume_text_with_links)

#     print("\n----- Parsed Resume JSON -----")
#     print(json.dumps(resume_dict, indent=2))

#     # --- Calculate total experience ---
#     total_exp_years = total_experience_from_resume(resume_dict.get("experience", []))
#     print(f"\n----- Total Experience (years) -----\n{total_exp_years:.2f} years")


def generate_jd_json(jd_text: str, *, api_key: str = None, model: str = "gemini-2.5-flash") -> dict:
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
    - Keep keys concise and descriptive.
    - Include only fields relevant to job qualifications.
    - Ensure pure JSON, no markdown, no commentary.

    Job Description Text:
    {jd_text}
    """

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

    # # ✅ ✅ ✅ RETURN FLAT JSON DIRECTLY (NO SCHEMA, NO FIELDS)
    # print("✅ Final JD JSON:")
    # print(parsed)

    return parsed

# # ---- Local Test -------
# if __name__ == "__main__":
#     sample_jd = """
#     Job Title: Data Scientist
#     Skills: Python, SQL, Machine Learning, Deep Learning
#     Education: B.Tech in Computer Science or equivalent
#     Experience: 2-4 years
#     Responsibilities:
#     - Build ML models
#     - Analyze data and generate insights
#     - Collaborate with cross-functional teams
#     Certifications: AWS Certified Machine Learning
#     Tools: TensorFlow, PowerBI
#     """
#     jd_json = generate_jd_json(sample_jd)
#     print("Parsed JD JSON:")
#     print(json.dumps(jd_json, indent=2))



def generate_score(
    resume_json: dict,
    jd_json: dict,
    weights: dict,
    resume_experience_float: float,
    resume_experience_formatted: str,
    *,
    api_key: str = None,
    model: str = "gemini-2.5-flash"
) -> dict:
    """
    Uses LLM ONLY for semantic evaluation.
    All math (total score) is done in Python to avoid hallucinations.
    """

    # ---- Extract JD fields dynamically ----
    field_list = list(jd_json.keys())

    # ---- LLM PROMPT (NO TOTAL, NO WEIGHTS) ----
    prompt = f"""
You are a resume evaluation assistant.

Compare the Resume JSON with the Job Description JSON and return structured evaluation.

Resume JSON:
{json.dumps(resume_json, indent=2)}

Job Description JSON:
{json.dumps(jd_json, indent=2)}

Candidate experience:
- Numeric (for comparison only): {resume_experience_float:.2f} years
- Display (use EXACTLY this text in summary): {resume_experience_formatted}

Rules:
- Do NOT invent experience formats
- Do NOT use decimals like 0.33 years
- Use ONLY the provided display experience text

Fields to evaluate:
{json.dumps(field_list, indent=2)}

Instructions:
1. For each field, return a score between 0 and 100 (inclusive).
2. Do NOT calculate total score.
3. Generate "overall_summary" with ONLY:
   a) Experience comparison with JD (less / equal / more)
   b) Where candidate does NOT meet JD
   c) Where candidate DOES meet JD
4. Keep it factual and neutral.
   - No hiring decision
   - No words like "strong fit", "expert", "ideal"
Note : Overall Summary must be covered in maximum 5 points 
5. Classify skills into:
   - matched_skills
   - missing_skills
   - other_skills

Return STRICT JSON only in this format:
{{
  "field_scores": {{
     "<field_name>": <float between 0 and 100>
  }},
  "overall_summary": ["string"],
  "matched_skills": ["string"],
  "missing_skills": ["string"],
  "other_skills": ["string"]
}}
"""

    # ---- Call LLM ----
    result = call_llm(prompt, model=model, api_key=api_key)

    # ---- Handle LLM error ----
    if not isinstance(result, dict) or result.get("error"):
        err = result.get("error", {})
        return {
            "field_scores": {field: 0.0 for field in field_list},
            "total": 0.0,
            "overall_summary": [f"LLM error: {err.get('message', str(err))}"],
            "matched_skills": [],
            "missing_skills": [],
            "other_skills": []
        }

    # ---- SAFE TOTAL SCORE CALCULATION (PYTHON) ----
    field_scores = result.get("field_scores", {})
    result["total"] = compute_total_score(field_scores, weights)

    return result

# # Testing code
# if __name__ == "__main__":
#     # Simulated LLM returned scores (0-100 per field)
#     llm_field_scores = {
#     "skills": 85,
#     "experience": 95,
#     "education": 80,
#     "certifications": 70,
#     "tools": 50,
#     "projects": 75,
#     "communication": 65,
#     "leadership": 60,
#     "problem_solving": 90,
#     "adaptability": 55
#     }

#     # Example user-provided weights (not normalized, can sum to > 1 or any number)
#     user_weights = {
#     "skills": 100,
#     "experience": 100,
#     "education": 50,
#     "certifications": 20,
#     "tools": 30,
#     "projects": 80,
#     "communication": 80,
#     "leadership": 60,
#     "problem_solving": 90,
#     "adaptability": 90
#     }

#     total = compute_total_score(llm_field_scores, user_weights)
#     print(f"Computed total score: {total}")
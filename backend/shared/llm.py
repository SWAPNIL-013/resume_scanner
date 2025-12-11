import json
from typing import Dict
from pydantic import ValidationError
from shared.schema import ResumeSchema,JobDescriptionSchema
from shared.utils import add_experience_duration_readable, call_llm

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
            {{"company": "string","role": "string","start_date": "YYYY-MM or empty string","end_date": "YYYY-MM, Present, or empty string","description": "string"}}
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


# # ------------------------------Generate JD JSON------------------------------
# def generate_jd_json(jd_text: str, *, api_key: str = None, model: str = "gemini-2.5-flash") -> dict:
#     """
#     Dynamically extract fields from a Job Description text using LLM.
#     Output: Flexible JSON with title + any relevant attributes (skills, experience, etc.)
#     """
#     prompt = f"""
#     You are an intelligent JD parser. Extract ALL relevant and meaningful fields from the given job description. 
#     Always return a valid JSON object.

#     Example structure (but it can vary dynamically):
#     {{
#         "title": "Data Scientist",
#         "skills": ["Python", "SQL", "ML"],
#         "education": "Bachelor's in Computer Science",
#         "experience": "2-4 years",
#         "responsibilities": ["Build ML models", "Analyze data"],
#         "certifications": ["AWS ML Foundations"],
#         "tools": ["TensorFlow", "PowerBI"]
#     }}

#     Guidelines:
#     - Keep keys concise and descriptive (e.g., skills, education, tools, domain, etc.).
#     - Include only fields relevant to job qualifications.
#     - Ensure pure JSON, no markdown, no commentary.

#     Job Description Text:
#     {jd_text}
#     """

#     # ✅ Use centralized LLM caller (handles retries & errors)
#     llm_result = call_llm(prompt, model=model, api_key=api_key)

#     if isinstance(llm_result, dict) and llm_result.get("error"):
#         print(f"JD parsing failed: {llm_result.get('error')}")
#         return {}

#     # ✅ Parse JSON safely
#     if isinstance(llm_result, dict):
#         parsed = llm_result
#     else:
#         try:
#             parsed = json.loads(llm_result)
#         except json.JSONDecodeError:
#             print("JD parsing failed: LLM returned non-JSON response")
#             return {}

#     # ✅ Normalize: title separate, rest dynamic
#     title = parsed.get("title", None)
#     fields = {k: v for k, v in parsed.items() if k.lower() != "title"}

#     try:
#         jd = JobDescriptionSchema(title=title, fields=fields)
#         return jd.model_dump()
#     except Exception as e:
#         print(f"JD schema validation failed: {e}")
#         return {"title": title, "fields": fields}

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

    # ✅ ✅ ✅ RETURN FLAT JSON DIRECTLY (NO SCHEMA, NO FIELDS)
    print("✅ Final JD JSON:")
    print(parsed)

    return parsed

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
    field_list = list(jd_json.keys())

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

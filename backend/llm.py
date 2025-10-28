import json
from typing import Dict
from pydantic import ValidationError
from schema import ResumeSchema
from utils import add_experience_duration_readable, call_llm

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


# ----------------- Test Runner -----------------
if __name__ == "__main__":
    import json
    from parser import extract_text_and_links  # your parser
    from utils import total_experience_from_resume

    resume_file = "samples/Naukri_Mr.IMRANSHARIFFHS[3y_8m].pdf"

    # Extract text + links
    resume_text, resume_links = extract_text_and_links(resume_file)

    print("----- Extracted Resume Text (first 500 chars) -----")
    print(resume_text[:500])

    print("\n----- Extracted Links -----")
    if resume_links:
        for link in resume_links:
            print(link)
    else:
        print("No links found")

    print("\n------- Running LLM to extract structured JSON ----------")
    resume_text_with_links = resume_text + "\n\nLinks found: " + ", ".join(resume_links)

    # Run LLM parser
    resume_dict = generate_resume_json(resume_text_with_links)

    print("\n----- Parsed Resume JSON -----")
    print(json.dumps(resume_dict, indent=2))

    # --- Calculate total experience ---
    total_exp_years = total_experience_from_resume(resume_dict.get("experience", []))
    print(f"\n----- Total Experience (years) -----\n{total_exp_years:.2f} years")

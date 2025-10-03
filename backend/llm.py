from schema import ResumeSchema
from utils import add_experience_duration_readable
from utils import call_llm

def generate_resume_json(text: str) -> dict:
    prompt = f"""
        You are a resume parser. Extract the following fields from the text and return JSON ONLY.

        Rules:
        - Only include **professional work experience or internships** in "experience".
        - Do NOT include hackathons, competitions, volunteering, or extracurricular activities in "experience".
        - If start_date or end_date are missing, set them as empty strings "".
        - For "urls", include only professional profile or project links (LinkedIn, GitHub, portfolio, project demos). Do NOT include email (mailto:) or phone (tel:) links.

        Output JSON schema:

        {{
            "name": "string",
            "email": "string",
            "phone": "string",
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

    parsed = call_llm(prompt)

    # validate + enrich
    resume = ResumeSchema.model_validate(parsed)
    resume_dict = resume.model_dump()
    resume_dict = add_experience_duration_readable(resume_dict)
    return resume_dict

# ----------------- Test Runner -----------------
if __name__ == "__main__":
    import json
    from parser import extract_text_and_links  # your parser
    from utils import total_experience_from_resume
    from llm import generate_resume_json

    resume_file = "samples/Sakshi_Kusmude_Resume (4).pdf"

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

    print("\n ------- Running LLM to extract structured JSON ----------")
    resume_text_with_links = resume_text + "\n\nLinks found: " + ", ".join(resume_links)

    # Run LLM parser
    resume_dict = generate_resume_json(resume_text_with_links)

    print("\n----- Parsed Resume JSON -----")
    print(json.dumps(resume_dict, indent=2))

    # --- Calculate total experience ---
    total_exp_years = total_experience_from_resume(resume_dict.get("experience", []))
    print(f"\n----- Total Experience (years) -----\n{total_exp_years:.2f} years")


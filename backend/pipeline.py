from parser import extract_text_and_links
from llm import generate_resume_json
from scoring_llm import generate_score
from utils import format_experience_years, total_experience_from_resume
import json


def run_pipeline(resume_file_path: str, weights: dict, jd_json: dict, *, username: str = None, api_key: str = None, model: str = "gemini-2.5-flash") -> dict:
    """
    Process a single resume against a pre-generated JD JSON.
    Passes api_key and model through to LLM calls so the frontend can supply them.
    """
    # 1) Extract resume text and links
    resume_text, resume_links = extract_text_and_links(resume_file_path)
    resume_text_with_links = resume_text + "\n\nLinks found: " + ", ".join(resume_links)

    # 2) Generate Resume JSON (use per-call API key/model if provided)
    resume_json = generate_resume_json(resume_text_with_links, api_key=api_key, model=model)

    # 3) Calculate total experience
    float_experience_years = total_experience_from_resume(resume_json.get("experience", []))
    total_experience_years = format_experience_years(float_experience_years)
    resume_json["total_experience_years"] = total_experience_years

    # 4) Score resume vs JD
    scored_result = generate_score(resume_json, jd_json, weights, float_experience_years, api_key=api_key, model=model)

    # 5) Compose final resume dict
    resume_dict = {
        **resume_json,
        "score": scored_result.get("total"),
        "remarks": scored_result.get("remarks", []),
        "scoring_breakdown": {
            "skills": scored_result.get("skills"),
            "experience": scored_result.get("experience"),
            "education": scored_result.get("education"),
            "certifications": scored_result.get("certifications"),
        },
        "matched_skills": scored_result.get("matched_skills", []),
        "missing_skills": scored_result.get("missing_skills", []),
        "other_skills": scored_result.get("other_skills", [])
    }

    return resume_dict


if __name__ == "__main__":
    # Quick smoke test (no external LLM calls expected unless api keys provided)
    jd_text = """
    Title: Data Scientist
    Skills: Python, Machine Learning, SQL
    Experience: 2 years
    """

    weights = {"skills": 0.4, "experience": 0.3, "education": 0.2, "certifications": 0.1}
    print("Generating JD JSON...")
    jd_json = generate_jd_json(jd_text)

    # No sample resumes by default - just print JD
    print(json.dumps(jd_json, indent=2))
# pipeline.py
from parser import extract_text_and_links
from llm import generate_resume_json
from scoring_llm import generate_score
from utils import format_experience_years, total_experience_from_resume
import json

def run_pipeline(resume_file_path: str, weights: dict, jd_json: dict, *, username: str = None, api_key: str = None, model: str = "gemini-2.5-flash") -> dict:
    """
    Process a single resume against a pre-generated JD JSON.
    """
    # 1️⃣ Extract resume text and links
    resume_text, resume_links = extract_text_and_links(resume_file_path)
    resume_text_with_links = resume_text + "\n\nLinks found: " + ", ".join(resume_links)
    print(f"The extracted text is :\n {resume_text_with_links} \nGenerating resume json through llm....") # logging statement

    # 2️⃣ Generate Resume JSON
    resume_json = generate_resume_json(resume_text_with_links)


    # 3️⃣ Calculate total experience
    float_experience_years = total_experience_from_resume(resume_json["experience"])
    total_experience_years=format_experience_years(float_experience_years)
    resume_json["total_experience_years"] = total_experience_years
    print(f"parsed resume : \n {resume_json} \nCalculating Score....") # logging statement 

    # 4️⃣ Score resume vs JD
    scored_result = generate_score(resume_json, jd_json, weights, float_experience_years)
    print(f"scored result :\n {scored_result}\n") # logging statement 


# 5️⃣ Combine final output
    resume_dict = {
        **resume_json,
        "score": scored_result.get("total"),
        "remarks": scored_result.get("remarks", []),
        "scoring_breakdown": {
            "skills": scored_result.get("skills"),
            "experience": scored_result.get("experience"),
            "education": scored_result.get("education"),
            "certifications": scored_result.get("certifications"),
        },
        "matched_skills": scored_result.get("matched_skills", []),
        "missing_skills": scored_result.get("missing_skills", []),
        "other_skills": scored_result.get("other_skills", [])
    }
    
    return resume_dict


# --------------------------
# Test runner
# --------------------------
if __name__ == "__main__":
    from jd_llm import generate_jd_json

    # ✅ Sample Job Description
    jd_text = """
    Title: Data Scientist
    Skills: Python, Machine Learning, Power BI, SQL,Docker
    Education: B.Tech in IT
    Experience: 2 years
    Responsibilities: Build ML models, Analyze datasets
    Certifications: AWS Machine Learning Foundations
    """

    # ✅ Sample weights
    weights = {
        "skills": 0.4,
        "experience": 0.3,
        "education": 0.2,
        "certifications": 0.1
    }

    # ✅ Pre-generate JD JSON once
    print("Generating JD JSON...")
    jd_json = generate_jd_json(jd_text)
    resume_json = generate_resume_json(resume_text_with_links, api_key=api_key, model=model)
    # ✅ List of sample resumes to test
    resume_files = [
        # "samples/Sakshi_Kusmude_Resume (4).pdf"
     "samples/Swapnil_Shete_Resume (3).pdf"
    ]

    # ✅ Process resumes
    results = []
    for resume_file in resume_files:
        print(f"\n[INFO] Processing resume: {resume_file}")
        result = run_pipeline(resume_file_path=resume_file, weights=weights, jd_json=jd_json)
        results.append(result)

    # ✅ Print results in readable JSON format
    print("\n🎯 Test Pipeline Results:")
    print(json.dumps(results, indent=2))
    

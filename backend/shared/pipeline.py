from backend.fetch_from_db_backend.db_fetcher import fetch_resumes
from backend.shared.utils import format_experience_years, total_experience_from_resume
import json
from backend.shared.parser import extract_text_and_links
from backend.shared.llm import generate_resume_json,generate_jd_json,generate_score



def run_pipeline_db(
    mongo_url,
    db_name,
    collection_name,
    weights: dict = None,
    jd_json:dict=None, 
    *,
    username=None,
    api_key=None,
    model="gemini-2.5-flash"
):
    print("Starting pipeline...\n")

    resumes = fetch_resumes(mongo_url, db_name, collection_name)
    processed_resumes = []

    for idx, resume_json in enumerate(resumes, start=1):
        resume_json.pop("_id", None)  # Remove Mongo-specific field

        # Calculate experience
        float_experience_years = total_experience_from_resume(resume_json.get("experience", []))
        total_experience_years = format_experience_years(float_experience_years)
        resume_json["total_experience_years"] = total_experience_years

        print("Starting Scoring...\n")
        # Score if JD present
        if jd_json:
            scored_result = generate_score(
                resume_json,
                jd_json,
                weights or {},
                float_experience_years,
                api_key=api_key,
                model=model,
            )
            resume_dict = {
                **resume_json,
                "jd_title": jd_json.get("title", ""),
                "score": scored_result.get("total"),
                "remarks": scored_result.get("remarks", []),
                "scoring_breakdown": scored_result.get("field_scores", {}),
                "matched_skills": scored_result.get("matched_skills", []),
                "missing_skills": scored_result.get("missing_skills", []),
                "other_skills": scored_result.get("other_skills", []),
            }
        else:
            resume_dict = {**resume_json}

        print(f"Resume JSON:{resume_json.get('name','')}\n")
        print(resume_json)  # prints the whole raw resume JSON

        print("\nProcessed Resume Details:")
        for key in ["jd_title", "score", "remarks", "scoring_breakdown", "matched_skills", "missing_skills", "other_skills"]:
            print(f"{key}: {resume_dict.get(key)}")
        print()  # extra newline for clarity


        processed_resumes.append(resume_dict)

    return processed_resumes




def run_pipeline(
    resume_file_path: str,
    weights: dict = None,
    jd_json: dict = None,
    *,
    username: str = None,
    api_key: str = None,
    model: str = "gemini-2.5-flash"
) -> dict:
    """
    Process a single resume.
    If JD is provided -> Full scoring pipeline.
    If JD is not provided -> Parse resume only (no scoring).
    """

    # 1️⃣ Extract text and links
    resume_text, resume_links = extract_text_and_links(resume_file_path)
    resume_text_with_links = resume_text + "\n\nLinks found: " + ", ".join(resume_links)
    print(f"Extracted text:\n{resume_text_with_links}\nGenerating resume JSON...")

    # 2️⃣ Generate Resume JSON
    resume_json = generate_resume_json(resume_text_with_links, api_key=api_key, model=model)

    # 3️⃣ Calculate total experience
    float_experience_years = total_experience_from_resume(resume_json.get("experience", []))
    total_experience_years = format_experience_years(float_experience_years)
    resume_json["total_experience_years"] = total_experience_years
    print(f"Parsed resume JSON:\n{resume_json}")

    # ✅ If JD is provided → Perform scoring
    if jd_json:
        print("JD detected — starting scoring process...")
        scored_result = generate_score(
            resume_json,
            jd_json,
            weights or {},
            float_experience_years,
            api_key=api_key,
            model=model,
        )

        resume_dict = {
            **resume_json,
            "jd_title": jd_json.get("title", ""),
            "score": scored_result.get("total"),
            "remarks": scored_result.get("remarks", []),
            "scoring_breakdown": scored_result.get("field_scores", {}),
            "matched_skills": scored_result.get("matched_skills", []),
            "missing_skills": scored_result.get("missing_skills", []),
            "other_skills": scored_result.get("other_skills", []),
        }

    # ⚙️ If JD not provided → only basic parsed resume
    else:
        print("No JD provided — skipping scoring.")
        resume_dict = {
            **resume_json            
        }

    return resume_dict


# --------------------------
# 🧪 Test Runner
# --------------------------
if __name__ == "__main__":
    jd_text = """
    Title: Data Scientist
    Skills: Python, Machine Learning, Power BI, SQL, Docker
    Education: B.Tech in IT
    Experience: 2 years
    Responsibilities: Build ML models, Analyze datasets
    Certifications: AWS Machine Learning Foundations
    Tools: TensorFlow, PowerBI
    """

    print("Generating JD JSON...")
    jd_json = generate_jd_json(jd_text)
    print("Parsed JD JSON:", json.dumps(jd_json, indent=2))

    # Example dynamic weights
    weights = {field: 1 / len(jd_json["fields"]) for field in jd_json["fields"]}

    # 🧾 Test with your local sample resume
    resume_files = ["samples/Swapnil_Shete_Resume (3).pdf"]
    results = []

    for resume_file in resume_files:
        print(f"\nProcessing resume: {resume_file}")
        result = run_pipeline(
            resume_file_path=resume_file,
            weights=weights,
            jd_json=jd_json
            
        )
        results.append(result)

    print("\n🎯 Final Results:")
    print(json.dumps(results, indent=2))

# --------------------------
# 🧪 Test Runner (NO JD MODE)
# --------------------------
if __name__ == "__main__":
    # No JD text or JD parsing here
    print("Running pipeline WITHOUT JD — only parsing resumes.")

    resume_files = ["samples/Swapnil_Shete_Resume (3).pdf"]
    results = []

    for resume_file in resume_files:
        print(f"\nProcessing resume: {resume_file}")
        result = run_pipeline(
            resume_file_path=resume_file,
            jd_json=None # ❌ No JD JSON
              
        )
        results.append(result)

    print("\n🧾 Parsed Resume Results:")
    print(json.dumps(results, indent=2))





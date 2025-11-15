import json
from parser import extract_text_and_links
from llm import generate_resume_json
from scoring_llm import generate_score
from utils import format_experience_years, total_experience_from_resume
from jd_llm import generate_jd_json 


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




# import json
# import logging
# from parser import extract_text_and_links
# from llm import generate_resume_json
# from scoring_llm import generate_score
# from utils import format_experience_years, total_experience_from_resume
# from jd_llm import generate_jd_json

# # ----------------------------------------------------------------------
# # 🧩 Logging Configuration
# # ----------------------------------------------------------------------
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s [%(threadName)s] %(levelname)s: %(message)s",
#     datefmt="%H:%M:%S"
# )
# logger = logging.getLogger(__name__)

# # ----------------------------------------------------------------------
# # 🧠 Main Pipeline
# # ----------------------------------------------------------------------
# def run_pipeline(
#     resume_file_path: str = None,
#     resume_bytes: bytes = None,
#     weights: dict = None,
#     jd_json: dict = None,
#     *,
#     username: str = None,
#     api_key: str = None,
#     model: str = "gemini-2.5-flash"
# ) -> dict:
#     """Thread-safe resume processing pipeline."""
#     try:
#         # 🟢 1. Extract text
#         logger.info(f"[{username or 'anon'}] Extracting text and links from {resume_file_path}")
#         resume_text, resume_links = extract_text_and_links(resume_bytes or resume_file_path)
#         if not resume_text.strip():
#             return {"error": {"message": "Empty resume text", "file": resume_file_path}}
#         logger.info(f"[{username or 'anon'}] Extracted resume text and links for {resume_file_path}")

#         # 🟢 2. Generate Resume JSON
#         logger.info(f"[{username or 'anon'}] Generating resume JSON for {resume_file_path}")
#         links_str = ", ".join(resume_links or [])
#         resume_json = generate_resume_json(
#             resume_text + "\nLinks: " + links_str,
#             api_key=api_key,
#             model=model
#         )
#         if "error" in resume_json:
#             return {
#                 "error": {
#                     "message": f"Resume parsing failed: {resume_json['error']['message']}",
#                     "file": resume_file_path
#                 }
#             }
#         logger.info(f"[{username or 'anon'}] Resume JSON generated for {resume_file_path}")

#         # 🟢 3. Experience calculation
#         logger.info(f"[{username or 'anon'}] Calculating total experience for {resume_file_path}")
#         years_float = total_experience_from_resume(resume_json.get("experience", []))
#         resume_json["total_experience_years"] = format_experience_years(years_float)
#         logger.info(f"[{username or 'anon'}] Experience calculation complete for {resume_file_path}")

#         # 🟢 4. Scoring (if JD provided)
#         if jd_json:
#             logger.info(f"[{username or 'anon'}] Scoring resume {resume_file_path}")
#             scored = generate_score(
#                 resume_json, jd_json, weights or {},
#                 years_float, api_key=api_key, model=model
#             )
#             if "error" in scored:
#                 return {
#                     "error": {
#                         "message": f"Scoring failed: {scored['error']['message']}",
#                         "file": resume_file_path
#                     }
#                 }
#             resume_json.update({
#                 "jd_title": jd_json.get("title", ""),
#                 "score": scored.get("total"),
#                 "remarks": scored.get("remarks", []),
#                 "scoring_breakdown": scored.get("field_scores", {}),
#                 "matched_skills": scored.get("matched_skills", []),
#                 "missing_skills": scored.get("missing_skills", []),
#                 "other_skills": scored.get("other_skills", []),
#             })
#             logger.info(f"[{username or 'anon'}] Scoring completed for {resume_file_path}")

#         logger.info(f"[{username or 'anon'}] ✅ Pipeline completed successfully for {resume_file_path}")
#         return {"data": resume_json, "file": resume_file_path}

#     except Exception as e:
#         logger.exception(f"❌ Pipeline crashed for {resume_file_path}: {e}")
#         return {"error": {"message": str(e), "file": resume_file_path}}


# # ----------------------------------------------------------------------
# # 🧪 LOCAL TEST RUNNER
# # ----------------------------------------------------------------------
# if __name__ == "__main__":
#     import concurrent.futures

#     jd_text = """
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

#     # Generate JD JSON once
#     print("🔹 Generating JD JSON...")
#     jd_json = generate_jd_json(jd_text)
#     print("Parsed JD JSON:", json.dumps(jd_json, indent=2))

#     # Example weight calculation
#     weights = {field: 1 / len(jd_json["fields"]) for field in jd_json.get("fields", {})}

#     # Resumes to test
#     resume_files = [
#         "samples/Swapnil_Shete_Resume (3).pdf",
#         "samples/Sakshi_Kusmude_Resume (4).pdf",
#         "samples/Naukri_Mr.IMRANSHARIFFHS[3y_8m].pdf"
#     ]

#     # Run concurrently to simulate real load
#     print("\n🚀 Running pipeline concurrently on multiple resumes...\n")
#     results = []
#     with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
#         futures = {
#             executor.submit(run_pipeline, resume_file_path=f, weights=weights, jd_json=jd_json): f
#             for f in resume_files
#         }
#         for future in concurrent.futures.as_completed(futures):
#             file = futures[future]
#             try:
#                 res = future.result()
#                 results.append(res)
#                 print(f"✅ Done: {file}")
#             except Exception as e:
#                 print(f"❌ Failed {file}: {e}")
#                 results.append({"error": str(e), "file": file})

#     print("\n🎯 Final Results:")
#     print(json.dumps(results, indent=2))

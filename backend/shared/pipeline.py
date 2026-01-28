from datetime import datetime, timezone
from backend.fetch_from_db_backend.db_fetcher import fetch_resumes
from backend.shared.parser import extract_text_and_links
from backend.shared.utils import (
    format_experience_years,
    total_experience_from_resume,
    build_evaluation,
)
from backend.shared.llm import generate_jd_json, generate_resume_json, generate_score
import json

def run_pipeline_db(
    document,
    weights: dict = None,
    jd_json: dict = None,
    *,
    username=None,
    api_key=None,
    model="gemini-2.5-flash"
):
    """
    Process a single resume document (from DB or file).
    Return a processed document with evaluations.
    """
    print("Starting pipeline...\n")

    resume_json=document.get("resume_json",{})
    evaluations=document.setdefault("evaluations",[])

    # 1️⃣ Experience calculation
    float_experience_years = total_experience_from_resume(
    resume_json.get("experience", [])
    )
    formatted_exp=format_experience_years(float_experience_years)
    resume_json["total_experience_years"] = formatted_exp
    resume_json.pop("uploaded_at", None)


        # 3️⃣ Scoring (only if JD present)
    if jd_json:
        print("Starting Scoring...\n")

        scored_result = generate_score(
                resume_json,
                jd_json,
                weights or {},
                float_experience_years,
                formatted_exp,
                api_key=api_key,
                model=model,
            )

        evaluation = build_evaluation(scored_result, jd_json)
        evaluations.append(evaluation)

    print("Scoring Completed...")

    return document



def run_pipeline(
    resume_file_path: str,
    weights: dict = None,
    jd_json: dict = None,
    *,
    username: str = None,
    api_key: str = None,
    model: str = "gemini-2.5-flash"
) -> dict:

    print("Starting Pipeline...")
    # 1️⃣ Extract text
    print("Extracting Text...")
    resume_text, resume_links = extract_text_and_links(resume_file_path)
    resume_text_with_links = resume_text + "\n\nLinks found: " + ", ".join(resume_links)

    # 2️⃣ LLM → resume JSON
    print("Generating Resume Json")
    resume_json = generate_resume_json(
        resume_text_with_links,
        api_key=api_key,
        model=model
    )

    # 3️⃣ Experience
    float_experience_years = total_experience_from_resume(
        resume_json.get("experience", [])
    )
    formatted_exp=format_experience_years(float_experience_years)
    resume_json["total_experience_years"] = formatted_exp
    resume_json["uploaded_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


    # 4️⃣ Final Document Strcture To Be Stored In DB
    document={
        "resume_json":resume_json,
        "evaluations":[]
    }

    # 5️⃣ Optional scoring
    if jd_json:
        scored_result = generate_score(
            resume_json,
            jd_json,
            weights or {},
            float_experience_years,
            formatted_exp,
            api_key=api_key,
            model=model,
        )

        evaluation = build_evaluation(scored_result, jd_json)
        document["evaluations"].append(evaluation)
    print(f"Document :\n{document}")
    return document

# import json

# # --------------------------
# # 🧪 Test Runner (WITH JD)
# # --------------------------
# if __name__ == "__main__":

#     jd_text = """
#     Title: Data Scientist
#     Skills: Python, Machine Learning, Power BI, SQL, Docker
#     Education: B.Tech in IT
#     Experience: 2 years
#     Responsibilities: Build ML models, Analyze datasets
#     Certifications: AWS Machine Learning Foundations
#     Tools: TensorFlow, PowerBI
#     """

#     print("Generating JD JSON...")
#     jd_json = generate_jd_json(jd_text)
#     print("Parsed JD JSON:")
#     print(json.dumps(jd_json, indent=2))

#     # ✅ Dynamic weights from JD keys
#     jd_keys = [k for k, v in jd_json.items() if v]
#     weights = {k: 1 / len(jd_keys) for k in jd_keys}

#     print("Generated Weights:")
#     print(json.dumps(weights, indent=2))

#     resume_files = [
#         "samples/Swapnil_Shete_Resume (3).pdf",
#         "samples/Swapnil_Shete_VIIT_PythonDev.pdf"
#     ]

#     results = []

#     for resume_file in resume_files:
#         print(f"\nProcessing resume: {resume_file}")

#         document = run_pipeline(
#             resume_file_path=resume_file,
#             weights=weights,
#             jd_json=jd_json
#         )

#         results.append(document)

#     print("\n🎯 Final Results (Stored Format):")
#     print(json.dumps(results, indent=2))




# import json

# # --------------------------
# # 🧪 Test Runner (NO JD MODE)
# # --------------------------
# if __name__ == "__main__":

#     print("Running pipeline WITHOUT JD — resume parsing only.")

#     resume_files = ["samples/Swapnil_Shete_Resume (3).pdf"]
#     results = []

#     for resume_file in resume_files:
#         print(f"\nProcessing resume: {resume_file}")

#         document = run_pipeline(
#             resume_file_path=resume_file,
#             jd_json=None
#         )

#         results.append(document)

#     print("\n🧾 Parsed Resume Results:")
#     print(json.dumps(results, indent=2))


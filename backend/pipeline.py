# # # pipeline with normal sequential processing

# # import json
# # from parser import extract_text_and_links
# # from llm import generate_resume_json
# # from scoring_llm import generate_score
# # from utils import format_experience_years, total_experience_from_resume
# # from jd_llm import generate_jd_json 


# # def run_pipeline(
# #     resume_file_path: str,
# #     weights: dict = None,
# #     jd_json: dict = None,
# #     *,
# #     username: str = None,
# #     api_key: str = None,
# #     model: str = "gemini-2.5-flash"
# # ) -> dict:
# #     """
# #     Process a single resume.
# #     If JD is provided -> Full scoring pipeline.
# #     If JD is not provided -> Parse resume only (no scoring).
# #     """

# #     # 1️⃣ Extract text and links
# #     resume_text, resume_links = extract_text_and_links(resume_file_path)
# #     resume_text_with_links = resume_text + "\n\nLinks found: " + ", ".join(resume_links)
# #     print(f"Extracted text:\n{resume_text_with_links}\nGenerating resume JSON...")

# #     # 2️⃣ Generate Resume JSON
# #     resume_json = generate_resume_json(resume_text_with_links, api_key=api_key, model=model)

# #     # 3️⃣ Calculate total experience
# #     float_experience_years = total_experience_from_resume(resume_json.get("experience", []))
# #     total_experience_years = format_experience_years(float_experience_years)
# #     resume_json["total_experience_years"] = total_experience_years
# #     print(f"Parsed resume JSON:\n{resume_json}")

# #     # ✅ If JD is provided → Perform scoring
# #     if jd_json:
# #         print("JD detected — starting scoring process...")
# #         scored_result = generate_score(
# #             resume_json,
# #             jd_json,
# #             weights or {},
# #             float_experience_years,
# #             api_key=api_key,
# #             model=model,
# #         )

# #         resume_dict = {
# #             **resume_json,
# #             "jd_title": jd_json.get("title", ""),
# #             "score": scored_result.get("total"),
# #             "remarks": scored_result.get("remarks", []),
# #             "scoring_breakdown": scored_result.get("field_scores", {}),
# #             "matched_skills": scored_result.get("matched_skills", []),
# #             "missing_skills": scored_result.get("missing_skills", []),
# #             "other_skills": scored_result.get("other_skills", []),
# #         }

# #     # ⚙️ If JD not provided → only basic parsed resume
# #     else:
# #         print("No JD provided — skipping scoring.")
# #         resume_dict = {
# #             **resume_json            
# #         }

# #     return resume_dict


# # # --------------------------
# # # 🧪 Test Runner WITH JD
# # # --------------------------
# # import time
# # def run_with_jd():
# #     start_time = time.time()   # ⏳ START TIMER

# #     jd_text = """
# #     Title: Data Scientist
# #     Skills: Python, Machine Learning, Power BI, SQL, Docker
# #     Education: B.Tech in IT
# #     Experience: 2 years
# #     Responsibilities: Build ML models, Analyze datasets
# #     Certifications: AWS Machine Learning Foundations
# #     Tools: TensorFlow, PowerBI
# #     """

# #     print("Generating JD JSON...")
# #     jd_json = generate_jd_json(jd_text)
# #     print("Parsed JD JSON:", json.dumps(jd_json, indent=2))

# #     # Dynamic weights
# #     weights = {field: 1 / len(jd_json["fields"]) for field in jd_json["fields"]}

# #     resume_files = [
# #         "samples/Swapnil_Shete_Resume (3).pdf",
# #         "samples/Sakshi_Kusmude_Resume (4).pdf",
# #         "samples/Naukri_Mr.IMRANSHARIFFHS[3y_8m].pdf"
# #     ]
# #     results = []

# #     for resume_file in resume_files:
# #         print(f"\nProcessing resume: {resume_file}")
# #         result = run_pipeline(
# #             resume_file_path=resume_file,
# #             weights=weights,
# #             jd_json=jd_json
# #         )
# #         results.append(result)

# #     print("\n🎯 Final Results:")
# #     print(json.dumps(results, indent=2))

# #     # END TIMER
# #     total_time = time.time() - start_time
# #     print(f"\n⏱️ Total Execution Time (WITH JD): {total_time:.2f} seconds")


# # # --------------------------
# # # 🧪 Test Runner WITHOUT JD
# # # --------------------------
# # def run_without_jd():
# #     start_time = time.time()   # ⏳ START TIMER

# #     print("Running pipeline WITHOUT JD — only parsing resumes.")

# #     resume_files = [
# #         "samples/Swapnil_Shete_Resume (3).pdf",
# #         "samples/Sakshi_Kusmude_Resume (4).pdf",
# #         "samples/Naukri_Mr.IMRANSHARIFFHS[3y_8m].pdf"
# #     ]
# #     results = []

# #     for resume_file in resume_files:
# #         print(f"\nProcessing resume: {resume_file}")
# #         result = run_pipeline(
# #             resume_file_path=resume_file,
# #             jd_json=None
# #         )
# #         results.append(result)

# #     print("\n🧾 Parsed Resume Results:")
# #     print(json.dumps(results, indent=2))

# #     total_time = time.time() - start_time
# #     print(f"\n⏱️ Total Execution Time (NO JD): {total_time:.2f} seconds")


# # # --------------------------
# # # MAIN ENTRY POINT
# # # --------------------------
# # if __name__ == "__main__":
# #     # Choose which one you want to run
# #     run_with_jd()
# #     # run_without_jd()



import logging
import threading
import os
import time
import concurrent.futures
import json
from parser import extract_text_and_links
from llm import generate_resume_json
from scoring_llm import generate_score
from utils import format_experience_years, total_experience_from_resume, validate_resume_json
from jd_llm import generate_jd_json

# Configure logging once
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------
# Main Pipeline
# ----------------------------------------------------------
def run_pipeline(
    resume_file_path: str,
    weights: dict = None,
    jd_json: dict = None,
    *,
    username: str = None,
    api_key: str = None,
    model: str = "gemini-2.5-flash"
) -> dict:

    thread_name = threading.current_thread().name
    thread_id = threading.get_ident()
    filename = os.path.basename(resume_file_path)

    try:
        # ------------------------------------------------------
        # 1. TEXT EXTRACTION
        # ------------------------------------------------------
        logger.info(f"[{thread_name}-{thread_id}] Starting text extraction for {filename}")
        resume_text, resume_links = extract_text_and_links(resume_file_path)

        if not resume_text or len(resume_text.strip()) < 20:
            msg = "Empty or invalid text extracted"
            logger.error(f"[{thread_name}-{thread_id}] ❌ {msg} for {filename}")
            return {"status": "failed", "error": msg, "file": filename}

        resume_text_with_links = resume_text + "\n\nLinks found: " + ", ".join(resume_links)
        logger.info(f"[{thread_name}-{thread_id}] ✅ Completed text extraction for {filename}")

        # ------------------------------------------------------
        # 2. RESUME JSON GENERATION
        # ------------------------------------------------------
        logger.info(f"[{thread_name}-{thread_id}] Starting resume JSON generation for {filename}")

        resume_json = generate_resume_json(
            resume_text_with_links,
            api_key=api_key,
            model=model
        )

        # Validate JSON
        validation_error = validate_resume_json(resume_json, filename)
        if validation_error:
            logger.error(f"[{thread_name}-{thread_id}] ❌ {validation_error} for {filename}")
            return {"status": "failed", "error": validation_error, "file": filename}

        logger.info(f"[{thread_name}-{thread_id}] ✅ Resume JSON validated for {filename}")

        # ------------------------------------------------------
        # 3. EXPERIENCE CALCULATION
        # ------------------------------------------------------
        logger.info(f"[{thread_name}-{thread_id}] Calculating total experience for {filename}")

        float_exp = total_experience_from_resume(resume_json.get("experience", []))
        formatted_exp = format_experience_years(float_exp)

        resume_json["total_experience_years"] = formatted_exp
        logger.info(f"[{thread_name}-{thread_id}] Experience: {formatted_exp}")

        # ------------------------------------------------------
        # 4. SCORING (if JD provided)
        # ------------------------------------------------------
        if jd_json:
            logger.info(f"[{thread_name}-{thread_id}] Starting scoring for {filename}")

            try:
                scored_result = generate_score(
                    resume_json,
                    jd_json,
                    weights or {},
                    float_exp,
                    api_key=api_key,
                    model=model,
                )
            except Exception as score_err:
                msg = f"Scoring failed: {score_err}"
                logger.error(f"[{thread_name}-{thread_id}] ❌ {msg} for {filename}")
                return {"status": "failed", "error": msg, "file": filename}

            if not isinstance(scored_result, dict) or "total" not in scored_result:
                msg = "Scoring JSON invalid/incomplete"
                logger.error(f"[{thread_name}-{thread_id}] ❌ {msg} for {filename}")
                return {"status": "failed", "error": msg, "file": filename}

            logger.info(f"[{thread_name}-{thread_id}] ✅ Scoring completed for {filename}")

            resume_dict = {
                **resume_json,
                "jd_title": jd_json.get("title", ""),
                "score": scored_result.get("total"),
                "remarks": scored_result.get("remarks", []),
                "scoring_breakdown": scored_result.get("field_scores", {}),
                "matched_skills": scored_result.get("matched_skills", []),
                "missing_skills": scored_result.get("missing_skills", []),
                "other_skills": scored_result.get("other_skills", []),
                "status": "success",
                "file": filename
            }

        else:
            logger.info(f"[{thread_name}-{thread_id}] Skipping scoring (JD not provided)")
            resume_dict = {**resume_json, "status": "success", "file": filename}

        # ------------------------------------------------------
        # Done
        # ------------------------------------------------------
        logger.info(f"[{thread_name}-{thread_id}] ✅ Finished processing {filename}")
        return resume_dict

    except Exception as e:
        logger.exception(f"[{thread_name}-{thread_id}] Pipeline crashed for {filename}: {e}")
        return {"status": "failed", "error": str(e), "file": filename}


# ----------------------------------------------------------
# Test runner
# ----------------------------------------------------------
def run_test():
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

    weights = {field: 1 / len(jd_json["fields"]) for field in jd_json["fields"]}

    resume_files = [
        "samples/Swapnil_Shete_Resume (3).pdf",
       "samples/hemalata.pdf"
    ]

    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(run_pipeline, resume_file_path=f, weights=weights, jd_json=jd_json): f
            for f in resume_files
        }
        results = []
        for future in concurrent.futures.as_completed(futures):
            file = futures[future]
            try:
                res = future.result()
                res["filename"] = file
                results.append(res)
                print(f"✅ Done processing: {file}")
            except Exception as exc:
                print(f"❌ Failed processing: {file} with error: {exc}")
                results.append({"status": "failed", "error": str(exc), "file": file})

    total_time = time.time() - start_time
    print("\nFinal results:")
    print(json.dumps(results, indent=2))
    print(f"\n⏱️ Total execution time: {total_time:.2f} seconds")
    print(f"Total resumes processed: {len(results)}")


if __name__ == "__main__":
    run_test()

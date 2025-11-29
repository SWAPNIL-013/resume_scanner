# pipeline_from_db.py

import json
from utils import format_experience_years, total_experience_from_resume
from scoring_llm import generate_score


def run_pipeline_from_db(
    resume_json: dict,
    *,
    jd_json: dict,
    weights: dict,
    username: str = None,
    api_key: str = None,
    model: str = "gemini-2.5-flash"
) -> dict:
    """
    Process a single resume JSON coming directly from MongoDB.
    JD + weights are mandatory.
    """

    print("🚀 Starting pipeline for one resume...")

    if not jd_json:
        raise ValueError("JD JSON is required for DB-based evaluation pipeline.")
    else:
        print("✅ JD JSON received.")

    if not weights:
        raise ValueError("Weights are required for DB-based evaluation pipeline.")
    else:
        print(f"✅ Weights received: {weights}")

    # Make sure JD is not mutated by scoring_llm
    jd_json = jd_json.copy()
    print(f"JD Title: {jd_json.get('title', '')}")
    print(f"Full JD JSON:\n{json.dumps(jd_json, indent=2)}")

    resume_id = resume_json.get("_id")
    print(f"Processing resume with _id: {resume_id}")

    # 1️⃣ Experience calculation
    float_exp = total_experience_from_resume(resume_json.get("experience", []))
    total_exp_formatted = format_experience_years(float_exp)
    resume_json["total_experience_years"] = total_exp_formatted
    print(f"Calculated total experience: {total_exp_formatted} years (raw: {float_exp})")

    # 2️⃣ Scoring
    print("Running scoring function...")
    scored = generate_score(
        resume_json,
        jd_json,
        weights,
        float_exp,
        username=username,
        api_key=api_key,
        model=model,
    )
    print(f"Scoring result: total score={scored.get('total')}")

    # 3️⃣ Final structured output
    result = {
        **resume_json,
        "resume_id": resume_id,
        "jd_title": jd_json.get("title", ""),
        "score": scored.get("total"),
        "remarks": scored.get("remarks", []),
        "scoring_breakdown": scored.get("field_scores", {}),
        "matched_skills": scored.get("matched_skills", []),
        "missing_skills": scored.get("missing_skills", []),
        "other_skills": scored.get("other_skills", []),
    }

    print("Pipeline completed for this resume.\n")
    return result

# pipeline.py
from parser import extract_text_and_links
from llm import generate_resume_json
from jd_llm import generate_jd_json
from scoring_llm import generate_score
from utils import total_experience_from_resume

def run_pipeline(resume_file_path: str, jd_text: str, weights: dict) -> dict:
    # 1️⃣ Extract resume text and links
    resume_text, resume_links = extract_text_and_links(resume_file_path)
    resume_text_with_links = resume_text + "\n\nLinks found: " + ", ".join(resume_links)
    print(f"The extracted text is :\n {resume_text_with_links} \nGenerating resume json through llm....") # logging statement

    # 2️⃣ Generate resume JSON
    resume_json = generate_resume_json(resume_text_with_links)

    # Calculate total experience
    resume_total_experience = total_experience_from_resume(resume_json["experience"])
    
    # add total experience in resume json 
    resume_json["total_experience_years"] = resume_total_experience

    print(f"parsed resume : \n {resume_json} \nGenerating jd json....") # logging statement 
    
    # 3️⃣ Generate JD JSON
    jd_json = generate_jd_json(jd_text)

    print(f"jd json is:\n {jd_json} \nCalculating score.... ") # logging statement 

    # 4️⃣ Get score from LLM
    scored_result = generate_score(resume_json, jd_json, weights, resume_total_experience)

    print(f"scored result :\n {scored_result}\n") # logging statement 


    resume_dict = {
    **resume_json,  # unpack original parsed resume
    "total_experience": resume_total_experience,
    "score": scored_result.get("total"),
    "remarks": scored_result.get("remarks", []),
    "scoring_breakdown": {
        "skills": scored_result.get("skills"),
        "experience": scored_result.get("experience"),
        "education": scored_result.get("education"),
        "certifications": scored_result.get("certifications"),
    }
}

    return resume_dict



# Test run
if __name__ == "__main__":
    resume_file = "samples/Sakshi_Kusmude_Resume (4).pdf"
    jd_text = """
    Title: Data Scientist
    Skills: Python, Machine Learning, Data Analysis, SQL
    Education: B.Tech in IT
    Experience: 2 years
    Responsibilities: Build ML models, Analyze datasets
    Certifications: AWS Machine Learning Foundations
    """
    weights = {
        "skills": 0.4,
        "experience": 0.3,
        "education": 0.2,
        "certifications": 0.1
    }

    pipeline_output = run_pipeline(resume_file, jd_text, weights)

    import json
    print(json.dumps(pipeline_output, indent=2))

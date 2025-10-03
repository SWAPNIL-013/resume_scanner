# main.py
from fastapi import FastAPI, UploadFile, File, Query, Body
from typing import List, Dict
from pydantic import BaseModel
from pipeline import run_pipeline
from exporter import export_to_excel, MASTER_FILE, get_new_excel_name
import tempfile
import shutil
from fastapi.responses import JSONResponse
import base64

app = FastAPI()

# --------------------------
# Standard weight defaults
# --------------------------
DEFAULT_WEIGHTS = {
    "skills": 0.4,
    "experience": 0.3,
    "education": 0.2,
    "certifications": 0.1
}

# --------------------------
# 1️⃣ Upload Resumes Only
# --------------------------
@app.post("/upload_resumes_only")
async def upload_resumes_only(files: List[UploadFile] = File(...)):
    uploaded_paths = []

    for file in files:
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
                shutil.copyfileobj(file.file, tmp)
                uploaded_paths.append(tmp.name)
        except Exception as e:
            print(f"⚠️ Failed to save {file.filename}: {e}")
            continue

    if not uploaded_paths:
        return {"status": "error", "message": "No valid resumes uploaded."}

    return {"status": "success", "uploaded_paths": uploaded_paths}

# --------------------------
# 2️⃣ Upload Job Description
# --------------------------
@app.post("/upload_jd")
async def upload_jd(
    jd_text: str = Query(..., description='Add Job Description as text'),
    skills_weight: float = Query(DEFAULT_WEIGHTS["skills"], ge=0, le=1),
    experience_weight: float = Query(DEFAULT_WEIGHTS["experience"], ge=0, le=1),
    education_weight: float = Query(DEFAULT_WEIGHTS["education"], ge=0, le=1),
    certifications_weight: float = Query(DEFAULT_WEIGHTS["certifications"], ge=0, le=1),
    save_mode: str = Query("new")
):
    jd_data = {
        "jd_text": jd_text,
        "weights": {
            "skills": skills_weight,
            "experience": experience_weight,
            "education": education_weight,
            "certifications": certifications_weight
        },
        "save_mode": save_mode
    }
    return {"status": "success", "jd_data": jd_data}

# --------------------------
# 3️⃣ Evaluate Resumes
# --------------------------
@app.post("/evaluate_resumes")
async def evaluate_resumes(
    uploaded_paths: List[str] = Body(..., description="List of uploaded resume file paths"),
    jd_data: dict = Body(..., description="JD text and weights")
):
    processed_resumes = []

    for path in uploaded_paths:
        try:
            resume_dict = run_pipeline(path, jd_data["jd_text"], jd_data["weights"])
            processed_resumes.append(resume_dict)
        except Exception as e:
            print(f"⚠️ Failed to process {path}: {e}")
            continue

    if not processed_resumes:
        return {"status": "error", "message": "No valid resumes to process."}

    return {"status": "success", "count": len(processed_resumes), "data": processed_resumes}


# --------------------------
# 4️⃣ Export to Excel
# --------------------------
class ExportRequest(BaseModel):
    processed_resumes: List[Dict]
    save_mode: str = "new"

@app.post("/export_resumes_excel")
async def export_resumes_excel(req: ExportRequest):
    processed_resumes = req.processed_resumes
    save_mode = req.save_mode

    # Determine Excel output file
    if save_mode.lower() == "append":
        output_file = MASTER_FILE
        append_flag = True
    else:
        output_file = get_new_excel_name()
        append_flag = False

    # Export resumes to Excel
    export_to_excel(processed_resumes, output_file, append=append_flag)

    # Convert Excel to base64 for download
    with open(output_file, "rb") as f:
        excel_bytes = f.read()
        excel_b64 = base64.b64encode(excel_bytes).decode("utf-8")

    return {
        "status": "success",
        "count": len(processed_resumes),
        "excel_file": excel_b64,
        "saved_path": output_file
    }

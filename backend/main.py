# main.py
from fastapi import FastAPI, UploadFile, File, Query, Body, Header, HTTPException, status
from typing import List
from schema import ExportRequest
from auth import register_user, authenticate_user, create_access_token, get_user_from_token
from pipeline import run_pipeline
from exporter import export_to_excel, get_new_excel_name, EXPORTS_DIR
from jd_llm import generate_jd_json
import tempfile
import shutil
from fastapi.responses import JSONResponse
import base64
import os

app = FastAPI()

# --------------------------
# Default Weights
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
async def upload_resumes_only(authorization: str = Header(None), files: List[UploadFile] = File(...), x_model: str = Header(None), x_api_key: str = Header(None)):
    # Authorization: Bearer <token>
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    token = authorization.split(" ")[-1]
    user = get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    uploaded_paths = []

    # create per-user upload dir
    user_dir = None
    if user and user.get("username"):
        user_dir = os.path.join(tempfile.gettempdir(), "resume_scanner_uploads", user.get("username"))
        os.makedirs(user_dir, exist_ok=True)

    for file in files:
        try:
            # save into per-user dir if available, else a tmp file
            if user_dir:
                dest = os.path.join(user_dir, file.filename)
                with open(dest, "wb") as out_f:
                    shutil.copyfileobj(file.file, out_f)
                uploaded_paths.append(dest)
            else:
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
    authorization: str = Header(None)
):
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    token = authorization.split(" ")[-1]
    user = get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    """
    Upload JD text and define weights. 
    (No save_mode here — handled during export)
    """
    jd_data = {
        "jd_text": jd_text,
        "weights": {
            "skills": skills_weight,
            "experience": experience_weight,
            "education": education_weight,
            "certifications": certifications_weight
        }
    }

    return {"status": "success", "jd_data": jd_data}


# --------------------------
# 3️⃣ Evaluate Resumes
# --------------------------
@app.post("/evaluate_resumes")
async def evaluate_resumes(
    uploaded_paths: List[str] = Body(..., description="List of uploaded resume file paths"),
    jd_data: dict = Body(..., description="JD text and weights"),
    authorization: str = Header(None),
    x_model: str = Header(None),
    x_api_key: str = Header(None)
):
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    token = authorization.split(" ")[-1]
    user = get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    processed_resumes = []

    # ✅ Generate JD JSON once
    print("Generating JD JSON...")
    # allow passing model/api key from frontend
    model = x_model or jd_data.get("model")
    api_key = x_api_key or jd_data.get("api_key")
    jd_json = generate_jd_json(jd_data["jd_text"], api_key=api_key, model=model)
    print(f"JD JSON is :\n{jd_json}\nEvaluating Resumes...\n ")

    # ✅ Process each resume using the same JD JSON
    for path in uploaded_paths:
        try:
            print(f"Processing: {path}")
            resume_dict = run_pipeline(
                path,
                weights=jd_data["weights"],
                jd_json=jd_json,
                username=user.get("username") if user else None,
                api_key=api_key,
                model=model
            )
            processed_resumes.append(resume_dict)
        except Exception as e:
            print(f"⚠️ Failed to process {path}: {e}")
            continue

    if not processed_resumes:
        return {"status": "error", "message": "No valid resumes to process."}

    return {"status": "success", "count": len(processed_resumes), "data": processed_resumes}


# --------------------------
# 4️⃣ Export Endpoint
# --------------------------
@app.post("/export_resumes_excel")
async def export_resumes_excel(req: ExportRequest, authorization: str = Header(None), x_model: str = Header(None), x_api_key: str = Header(None)):
    # Expect Authorization header: Bearer <token>
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    token = authorization.split(" ")[-1]
    user = get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    try:
        # determine user base export directory
        user_base = None
        if user and user.get("username"):
            user_base = os.path.join(EXPORTS_DIR, user.get("username"))
            os.makedirs(user_base, exist_ok=True)

        if req.file_path:
            # ensure filename is basename, stored in user_base if available
            if user_base:
                req.file_path = os.path.join(user_base, os.path.basename(req.file_path))
            else:
                req.file_path = os.path.join(EXPORTS_DIR, os.path.basename(req.file_path))

        df = export_to_excel(
            resume_list=req.processed_resumes,
            mode=req.mode,
            file_path=req.file_path,
            sheet_name=req.sheet_name,
            base_dir=user_base
        )

        output_file = req.file_path
        if req.mode == "new_file" and not req.file_path:
            output_file = get_new_excel_name(base_dir=user_base)

        # Convert Excel to base64
        with open(output_file, "rb") as f:
            excel_bytes = f.read()
            excel_b64 = base64.b64encode(excel_bytes).decode("utf-8")

        return {
            "status": "success",
            "count": len(req.processed_resumes),
            "excel_file": excel_b64,
            "saved_path": output_file
        }

    except FileNotFoundError as e:
        return {"status": "error", "message": str(e)}
    except ValueError as e:
        return {"status": "error", "message": str(e)}
    except Exception as e:
        return {"status": "error", "message": f"Unexpected error: {str(e)}"}


@app.post("/register")
async def register(username: str = Query(...), password: str = Query(...), full_name: str = Query(None)):
    created = register_user(username, password, full_name)
    if not created:
        raise HTTPException(status_code=400, detail="User already exists")
    return {"status": "success", "message": "User registered"}


@app.post("/login")
async def login(username: str = Query(...), password: str = Query(...)):
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"username": user["username"]})
    return {"access_token": token, "token_type": "bearer"}

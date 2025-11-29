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
from mongo_exporter import export_to_mongo
from pipeline import run_pipeline_db


app = FastAPI()


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


# --------------------------
# 1️⃣ Upload Resumes Only
# --------------------------
@app.post("/upload_resumes_only")
async def upload_resumes_only(authorization: str = Header(None), files: List[UploadFile] = File(...), x_model: str = Header(None), x_api_key: str = Header(None)):
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
    jd_text: str = Body(..., description="Job Description text"),
    weights: dict = Body(..., description="Dynamic weights for JD fields"),
    authorization: str = Header(None)
):
    """
    Upload JD text and define dynamic weights (coming from frontend).
    Example Body:
    {
        "jd_text": "We are hiring a data scientist...",
        "weights": {
            "skills": 0.3,
            "education": 0.1,
            "tools": 0.2,
            "projects": 0.4
        }
    }
    """
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    token = authorization.split(" ")[-1]
    user = get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    jd_data = {
        "jd_text": jd_text,
        "weights": weights
    }

    return {"status": "success", "jd_data": jd_data}




# --------------------------
# 3️⃣ Evaluate Resumes
# --------------------------
@app.post("/evaluate_resumes")
async def evaluate_resumes(
    uploaded_paths: List[str] = Body(..., description="List of uploaded resume file paths"),
    jd_data: dict = Body(None, description="JD text and weights (optional)"),
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

    # ✅ Setup model and API key
    model = (x_model or (jd_data and jd_data.get("model")) or "gemini-2.5-flash")
    api_key = (x_api_key or (jd_data and jd_data.get("api_key")))

    # ✅ JD JSON (optional)
    jd_json = None
    if jd_data and "jd_text" in jd_data and jd_data["jd_text"].strip():
        print("Generating JD JSON...")
        jd_json = generate_jd_json(jd_data["jd_text"], api_key=api_key, model=model)
        print(f"JD JSON is :\n{jd_json}\nEvaluating Resumes...\n ")
    else:
        print("⚙️ No JD provided — running resume parsing only mode.\n")

    # ✅ Process each resume
    for path in uploaded_paths:
        try:
            print(f"Processing: {path}")
            resume_dict = run_pipeline(
                resume_file_path=path,
                weights=(jd_data.get("weights") if jd_data else None),
                jd_json=jd_json,  # may be None
                username=user.get("username"),
                api_key=api_key,
                model=model
            )
            processed_resumes.append(resume_dict)
        except Exception as e:
            print(f"⚠️ Failed to process {path}: {e}")
            continue

    if not processed_resumes:
        return {"status": "error", "message": "No valid resumes to process."}

    return {
        "status": "success",
        "count": len(processed_resumes),
        "data": processed_resumes,
        "jd_mode": "enabled" if jd_json else "disabled"
     }

@app.post("/evaluate_resumes_db")
async def evaluate_resumes_db(
    mongo_uri: str = Body(...),
    db_name: str = Body(...),
    collection_name: str = Body(...),
    jd_data: dict = Body(None),
    authorization: str = Header(None),
    x_model: str = Header(None),
    x_api_key: str = Header(None),
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = authorization.split(" ")[-1]
    user = get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    model = x_model or (jd_data and jd_data.get("model")) or "gemini-2.5-flash"
    api_key = x_api_key or (jd_data and jd_data.get("api_key"))

    try:
        processed_resumes = run_pipeline_db(
            mongo_uri=mongo_uri,
            db_name=db_name,
            collection_name=collection_name,
            weights=jd_data.get("weights") if jd_data else None,
            jd_text=jd_data.get("jd_text") if jd_data else None,  # Pass jd_text here
            username=user.get("username"),
            api_key=api_key,
            model=model,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline processing failed: {e}")

    if not processed_resumes:
        return {"status": "error", "message": "No valid resumes to process."}

    return {
        "status": "success",
        "count": len(processed_resumes),
        "data": processed_resumes,
        "jd_mode": "enabled" if jd_data and jd_data.get("jd_text") else "disabled",
    }




# --------------------------
# 4️⃣ Export Endpoint
# --------------------------
@app.post("/export_resumes_excel")
async def export_resumes_excel(req: ExportRequest, authorization: str = Header(None), x_model: str = Header(None), x_api_key: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    token = authorization.split(" ")[-1]
    user = get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    try:
        user_base = None
        if user and user.get("username"):
            user_base = os.path.join(EXPORTS_DIR, user.get("username"))
            os.makedirs(user_base, exist_ok=True)

        if req.file_path:
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



# --------------------------
# 5️⃣ Export to MongoDB
# --------------------------
@app.post("/export_resumes_mongo")
async def export_resumes_mongo(req: dict, authorization: str = Header(None)):
    """
    req = {
        "processed_resumes": [...],
        "mongo_url": "mongodb+srv://user:pass@cluster/dbname",
        "db_name": "resume_db",
        "collection_name": "resumes"
    }
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    try:
        mongo_url = req.get("mongo_url")
        db_name = req.get("db_name", "resume_db")
        collection_name = req.get("collection_name", "resumes")
        resume_list = req.get("processed_resumes", [])

        if not mongo_url:
            raise ValueError("MongoDB URL missing")

        result = export_to_mongo(resume_list, mongo_url, db_name, collection_name)
        print("✅ Data export received for MongoDB")
        return {
            "status": "success",
            "inserted_count": result["inserted_count"],
            "db_name": db_name,
            "collection_name": collection_name
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}



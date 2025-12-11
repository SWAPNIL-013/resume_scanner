from fastapi import APIRouter, FastAPI, UploadFile, File, Query, Body, Header, HTTPException, status
from typing import List
from shared.schema import ExportRequest
from shared.auth import register_user, authenticate_user, create_access_token, get_user_from_token
from shared.exporter import export_to_excel, get_new_excel_name, EXPORTS_DIR,export_to_mongo
from shared.llm import generate_jd_json
import base64
import os
from shared.pipeline import run_pipeline_db
from pymongo import MongoClient



router=APIRouter()


@router.post("/register")
async def register(username: str = Query(...), password: str = Query(...), full_name: str = Query(None)):
    created = register_user(username, password, full_name)
    if not created:
        raise HTTPException(status_code=400, detail="User already exists")
    return {"status": "success", "message": "User registered"}


@router.post("/login")
async def login(username: str = Query(...), password: str = Query(...)):
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"username": user["username"]})
    return {"access_token": token, "token_type": "bearer"}





# --------------------------
# 1️⃣ Connect to MongoDB
# --------------------------
@router.post("/connect_mongo")
async def connect_mongo(
    mongo_url: str = Body(..., description="MongoDB connection URI"),
    db_name: str = Body(..., description="Database name"),
    collection_name: str = Body(..., description="Collection name"),
    authorization: str = Header(None)
):
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    token = authorization.split(" ")[-1]
    user = get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    try:
        client = MongoClient(mongo_url)
        db = client[db_name]
        collection = db[collection_name]
        resume_count = collection.count_documents({})
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    print(f"Connection successful : Resume Count = {resume_count}")
    return {"status": "success", "resume_count": resume_count}



# --------------------------
# 2️⃣ Upload Job Description 
# --------------------------
@router.post("/upload_jd")
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
@router.post("/evaluate_resumes_db")
async def evaluate_resumes_db(
    mongo_url: str = Body(...),
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
            mongo_url=mongo_url,
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
@router.post("/export_resumes_excel")
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
@router.post("/export_resumes_mongo")
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



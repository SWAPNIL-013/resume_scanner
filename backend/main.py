from fastapi import FastAPI, UploadFile, File, Query, Body, Header, HTTPException, status
from typing import List
from parser import extract_text_from_jd
from schema import ExportRequest,RegisterRequest,LoginRequest
from auth import  approve_user, deny_user, get_all_users, get_pending_users,register_user, authenticate_user, create_access_token, get_user_from_token, update_user_role
from pipeline import run_pipeline
from exporter import export_to_excel, get_new_excel_name, EXPORTS_DIR
from llm import generate_jd_json
import tempfile
import shutil
from fastapi.responses import JSONResponse
import base64
import os
from mongo_exporter import export_to_mongo
import json
app = FastAPI()

# -----------------------------
# ✅ REGISTER
# -----------------------------
@app.post("/register")
async def register(user: RegisterRequest):
    created = register_user(
        user.username,
        user.password,
        user.full_name,
        role="user"
    )

    if not created:
        raise HTTPException(status_code=400, detail="User already exists")

    return {"status": "success", "message": "User registered, waiting for admin approval"}


# -----------------------------
# ✅ LOGIN
# -----------------------------
@app.post("/login")
async def login(user: LoginRequest):
    user_data = authenticate_user(user.username, user.password)

    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user_data.get("error") == "not_approved":
        raise HTTPException(status_code=403, detail="Admin approval pending")

    if user_data.get("error") == "denied":
        raise HTTPException(status_code=403, detail="Your request was denied")


    token = create_access_token({
        "username": user_data["username"],
        "role": user_data.get("role", "user")
    })

    return {"access_token": token, "token_type": "bearer"}


# -----------------------------
# ✅ CURRENT USER
# -----------------------------
@app.get("/me")
async def me(authorization: str = Header(None)):
    token = authorization.replace("Bearer ", "")
    user = get_user_from_token(token)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    return user


# -----------------------------
# ✅ ADMIN: PENDING USERS
# -----------------------------
@app.get("/admin/pending-users")
async def pending_users(authorization: str = Header(None)):
    token = authorization.replace("Bearer ", "")
    user = get_user_from_token(token)

    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    return get_pending_users()

@app.get("/admin/users")
async def all_users(authorization: str = Header(None)):
    token = authorization.replace("Bearer ", "")
    user = get_user_from_token(token)

    if not user or user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    return get_all_users()

# -----------------------------
# ✅ ADMIN: APPROVE USER
# -----------------------------
@app.post("/admin/approve/{username}")
async def approve(username: str, authorization: str = Header(None)):
    token = authorization.replace("Bearer ", "")
    user = get_user_from_token(token)

    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    approved = approve_user(username)

    if not approved:
        raise HTTPException(status_code=400, detail="Approval failed")

    return {"message": "User approved"}

@app.post("/admin/deny/{username}")
async def deny(username: str, authorization: str = Header(None)):
    token = authorization.replace("Bearer ", "")
    admin = get_user_from_token(token)

    if not admin or admin["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    return {"denied": deny_user(username)}


@app.post("/admin/change-role/{username}")
async def change_role(username: str, role: str, authorization: str = Header(None)):
    token = authorization.replace("Bearer ", "")
    admin = get_user_from_token(token)

    if not admin or admin["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    return {"updated": update_user_role(username, role)}





# @app.post("/register")
# async def register(user: RegisterRequest):
#     created = register_user(user.username, user.password, user.full_name, role="user")
#     if not created:
#         raise HTTPException(status_code=400, detail="User already exists")
#     return {"message": "Registered. Waiting for admin approval"}


# @app.post("/login")
# async def login(user: LoginRequest):
#     user_data = authenticate_user(user.username, user.password)

#     if not user_data:
#         raise HTTPException(status_code=401, detail="Invalid credentials")

#     if user_data.get("error") == "pending":
#         raise HTTPException(status_code=403, detail="Admin approval pending")

#     if user_data.get("error") == "denied":
#         raise HTTPException(status_code=403, detail="Your request was denied")

#     token = create_access_token({
#         "username": user_data["username"],
#         "role": user_data["role"]
#     })

#     return {"access_token": token}


# @app.get("/me")
# async def me(authorization: str = Header(None)):
#     token = authorization.replace("Bearer ", "")
#     user = get_user_from_token(token)
#     if not user:
#         raise HTTPException(status_code=401, detail="Invalid token")
#     return user


# # -----------------------------
# # ✅ ADMIN APIs
# # -----------------------------
# @app.get("/admin/users")
# async def all_users(authorization: str = Header(None)):
#     token = authorization.replace("Bearer ", "")
#     admin = get_user_from_token(token)

#     if not admin or admin["role"] != "admin":
#         raise HTTPException(status_code=403, detail="Admin only")

#     return get_all_users()


# @app.post("/admin/approve/{username}")
# async def approve(username: str, authorization: str = Header(None)):
#     token = authorization.replace("Bearer ", "")
#     admin = get_user_from_token(token)

#     if not admin or admin["role"] != "admin":
#         raise HTTPException(status_code=403, detail="Admin only")

#     return {"approved": approve_user(username)}


# @app.post("/admin/deny/{username}")
# async def deny(username: str, authorization: str = Header(None)):
#     token = authorization.replace("Bearer ", "")
#     admin = get_user_from_token(token)

#     if not admin or admin["role"] != "admin":
#         raise HTTPException(status_code=403, detail="Admin only")

#     return {"denied": deny_user(username)}


# @app.post("/admin/change-role/{username}")
# async def change_role(username: str, role: str, authorization: str = Header(None)):
#     token = authorization.replace("Bearer ", "")
#     admin = get_user_from_token(token)

#     if not admin or admin["role"] != "admin":
#         raise HTTPException(status_code=403, detail="Admin only")

#     return {"updated": update_user_role(username, role)}


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


@app.post("/upload_jd")
async def upload_jd(
    file: UploadFile = File(...),
    authorization: str = Header(None),
    x_model: str = Header(None),
    x_api_key: str = Header(None)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.split(" ")[-1]
    user = get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    model = x_model or "gemini-2.5-flash"
    api_key = x_api_key

    # ✅ Create temporary file for JD
    with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        temp_path = temp_file.name

    try:
        # ✅ Extract JD text
        jd_text = extract_text_from_jd(temp_path)

        # ✅ Convert JD → JD JSON
        jd_json = generate_jd_json(jd_text, api_key=api_key, model=model)
        print(json.dumps(jd_json, indent=2))

        # ✅ Extract ONLY JD fields for slider creation
        jd_fields = list(jd_json.keys())

        return {
            "status": "success",
            "jd_fields": jd_fields,
            "jd_json": jd_json
        }

    finally:
        # ✅ Always cleanup temp file
        try:
            os.remove(temp_path)
        except:
            pass

@app.post("/evaluate_resumes")
async def evaluate_resumes(
    uploaded_paths: List[str] = Body(..., description="List of uploaded resume file paths"),
    jd_data: dict = Body(None, description="Contains jd_json + weights"),
    authorization: str = Header(None),
    x_model: str = Header(None),
    x_api_key: str = Header(None)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.split(" ")[-1]
    user = get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    processed_resumes = []

    model = x_model or "gemini-2.5-flash"
    api_key = x_api_key

    # ✅ JD JSON + weights now come directly from frontend
    jd_json = jd_data.get("jd_json") if jd_data else None
    weights = jd_data.get("weights") if jd_data else None

    if jd_json:
        print("✅ JD JSON received — scoring enabled\n")
    else:
        print("⚙️ No JD provided — resume parsing only mode\n")

    for path in uploaded_paths:
        try:
            resume_dict = run_pipeline(
                resume_file_path=path,
                weights=weights,
                jd_json=jd_json,
                username=user.get("username"),
                api_key=api_key,
                model=model
            )
            processed_resumes.append(resume_dict)

        except Exception as e:
            print(f"⚠️ Failed to process {path}: {e}")

    if not processed_resumes:
        return {"status": "error", "message": "No valid resumes to process."}

    return {
        "status": "success",
        "count": len(processed_resumes),
        "data": processed_resumes,
        "jd_mode": "enabled" if jd_json else "disabled"
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




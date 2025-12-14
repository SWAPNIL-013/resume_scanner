from fastapi import APIRouter, HTTPException, Header
from shared.auth import approve_user, authenticate_user, create_access_token, deny_user, get_all_users, get_pending_users, get_user_from_token, register_user, update_user_role
from shared.schema import LoginRequest, RegisterRequest


router=APIRouter()

# -----------------------------
# ✅ REGISTER
# -----------------------------
@router.post("/register")
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
@router.post("/login")
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
@router.get("/me")
async def me(authorization: str = Header(None)):
    token = authorization.replace("Bearer ", "")
    user = get_user_from_token(token)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    return user


# -----------------------------
# ✅ ADMIN: PENDING USERS
# -----------------------------
@router.get("/admin/pending-users")
async def pending_users(authorization: str = Header(None)):
    token = authorization.replace("Bearer ", "")
    user = get_user_from_token(token)

    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    return get_pending_users()

@router.get("/admin/users")
async def all_users(authorization: str = Header(None)):
    token = authorization.replace("Bearer ", "")
    user = get_user_from_token(token)

    if not user or user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    return get_all_users()

# -----------------------------
# ✅ ADMIN: APPROVE USER
# -----------------------------
@router.post("/admin/approve/{username}")
async def approve(username: str, authorization: str = Header(None)):
    token = authorization.replace("Bearer ", "")
    user = get_user_from_token(token)

    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    approved = approve_user(username)

    if not approved:
        raise HTTPException(status_code=400, detail="Approval failed")

    return {"message": "User approved"}

@router.post("/admin/deny/{username}")
async def deny(username: str, authorization: str = Header(None)):
    token = authorization.replace("Bearer ", "")
    admin = get_user_from_token(token)

    if not admin or admin["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    return {"denied": deny_user(username)}


@router.post("/admin/change-role/{username}")
async def change_role(username: str, role: str, authorization: str = Header(None)):
    token = authorization.replace("Bearer ", "")
    admin = get_user_from_token(token)

    if not admin or admin["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    return {"updated": update_user_role(username, role)}


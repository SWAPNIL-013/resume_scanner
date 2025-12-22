from fastapi import APIRouter, HTTPException, Header
from backend.shared.auth import approve_user, deny_user, get_all_users, get_pending_users, get_user_from_token,update_user_role



router=APIRouter()


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


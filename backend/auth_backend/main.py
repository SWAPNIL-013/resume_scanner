# -----------------------------
# ✅ REGISTER
# -----------------------------
from fastapi import HTTPException,APIRouter, Header
from shared.auth import authenticate_user, create_access_token, get_user_from_token, register_user
from shared.schema import LoginRequest, RegisterRequest

router=APIRouter()

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

    return {"access_token": token, "token_type": "bearer", "role": user_data.get("role", "user") }

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

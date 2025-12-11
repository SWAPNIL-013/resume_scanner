# import os
# from dotenv import load_dotenv
# from typing import Dict, Optional
# from datetime import datetime, timedelta
# from passlib.context import CryptContext
# import jwt
# from pymongo import MongoClient
# from pymongo.errors import DuplicateKeyError

# # -----------------------------
# # ✅ LOAD ENVIRONMENT VARIABLES
# # -----------------------------
# load_dotenv()

# # -----------------------------
# # ✅ MONGODB SETUP
# # -----------------------------
# MONGO_URL = os.getenv("MONGO_URL")
# if not MONGO_URL:
#     raise ValueError("MONGO_URL is not set in environment variables")

# MONGO_DB = "Users_db"
# MONGO_USERS_COLLECTION = "users"

# client = MongoClient(MONGO_URL)
# db = client[MONGO_DB]
# users_collection = db[MONGO_USERS_COLLECTION]

# # -----------------------------
# # ✅ JWT SETTINGS
# # -----------------------------
# JWT_SECRET = os.getenv("JWT_SECRET", "devsecret")
# JWT_ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 180

# pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# # -----------------------------
# # ✅ REGISTER USER
# # -----------------------------
# def register_user(
#     username: str,
#     password: str,
#     full_name: Optional[str] = None,
#     role: str = "user"
# ) -> bool:
#     hashed = pwd_context.hash(password)
#     user_doc = {
#         "_id": username,
#         "username": username,
#         "password": hashed,
#         "full_name": full_name,
#         "role": role,
#         "is_approved": True if role == "admin" else False,
#         "created_at": datetime.utcnow()
#     }

#     try:
#         users_collection.insert_one(user_doc)
#         return True
#     except DuplicateKeyError:
#         return False


# # -----------------------------
# # ✅ LOGIN AUTH
# # -----------------------------
# def authenticate_user(username: str, password: str) -> Optional[Dict]:
#     user = users_collection.find_one({"_id": username})
#     if not user:
#         return None
#     if not pwd_context.verify(password, user["password"]):
#         return None

#     if not user.get("is_approved", False):
#         return {"error": "not_approved"}

#     return {
#         "username": user["username"],
#         "full_name": user.get("full_name"),
#         "role": user.get("role", "user")
#     }


# # -----------------------------
# # ✅ JWT HELPERS
# # -----------------------------
# def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
#     to_encode = data.copy()

#     expire = datetime.utcnow() + (
#         expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     )

#     to_encode.update({"exp": expire})
#     return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


# def decode_access_token(token: str) -> Optional[dict]:
#     try:
#         return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
#     except Exception:
#         return None


# def get_user_from_token(token: str) -> Optional[Dict]:
#     payload = decode_access_token(token)
#     if not payload:
#         return None
#     username = payload.get("username")
#     if not username:
#         return None

#     user = users_collection.find_one({"_id": username})
#     if not user:
#         return None

#     return {
#         "username": user["username"],
#         "full_name": user.get("full_name",None),
#         "role": user.get("role", "user"),
#         "is_approved": user.get("is_approved", False)
#     }


# # -----------------------------
# # ✅ ADMIN HELPERS
# # -----------------------------
# def get_all_users():
#     return list(users_collection.find({}, {"password": 0}))

# def get_pending_users():
#     return list(users_collection.find({"is_approved": False}, {"password": 0}))

# def approve_user(username: str):
#     result = users_collection.update_one(
#         {"_id": username},
#         {"$set": {"is_approved": True}}
#     )
#     return result.modified_count > 0

# def deny_user(username: str):
#     result= users_collection.update_one(
#         {"_id": username}, {"$set": {"is_approved": False}}
#     )
#     return result.modified_count > 0


# def update_user_role(username: str, role: str):
#     result= users_collection.update_one(
#         {"_id": username}, {"$set": {"role": role}}
#     )
#     return result.modified_count > 0


import os
from dotenv import load_dotenv
from typing import Dict, Optional
from datetime import datetime, timedelta

from passlib.context import CryptContext
import jwt
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

# -----------------------------
# ✅ LOAD ENVIRONMENT VARIABLES
# -----------------------------
load_dotenv()

# -----------------------------
# ✅ MONGODB SETUP
# -----------------------------
MONGO_URL = os.getenv("MONGO_URL")
if not MONGO_URL:
    raise ValueError("MONGO_URL is not set in environment variables")

MONGO_DB = "Users_db"
MONGO_USERS_COLLECTION = "users"

client = MongoClient(MONGO_URL)
db = client[MONGO_DB]
users_collection = db[MONGO_USERS_COLLECTION]

# -----------------------------
# ✅ JWT SETTINGS
# -----------------------------
JWT_SECRET = os.getenv("JWT_SECRET", "devsecret")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 180  # 3 hours

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# -----------------------------
# ✅ REGISTER USER
# -----------------------------
def register_user(
    username: str,
    password: str,
    full_name: Optional[str] = None,
    role: str = "user"
) -> bool:
    hashed = pwd_context.hash(password)

    user_doc = {
        "_id": username,
        "username": username,
        "password": hashed,
        "full_name": full_name,
        "role": role,
        "is_approved": True if role == "admin" else False,
        "created_at": datetime.utcnow()
    }

    try:
        users_collection.insert_one(user_doc)
        return True
    except DuplicateKeyError:
        return False


# -----------------------------
# ✅ LOGIN AUTH
# -----------------------------
def authenticate_user(username: str, password: str) -> Optional[Dict]:
    user = users_collection.find_one({"_id": username})
    if not user:
        return None

    if not pwd_context.verify(password, user["password"]):
        return None

    if not user.get("is_approved", False):
        return {"error": "not_approved"}

    return {
        "username": user["username"],
        "full_name": user.get("full_name"),
        "role": user.get("role", "user")
    }


# -----------------------------
# ✅ JWT HELPERS
# -----------------------------
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()

    expire = datetime.utcnow() + (
        expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        return None


def get_user_from_token(token: str) -> Optional[Dict]:
    payload = decode_access_token(token)
    if not payload:
        return None

    username = payload.get("username")
    if not username:
        return None

    user = users_collection.find_one({"_id": username})
    if not user:
        return None

    return {
        "username": user["username"],
        "full_name": user.get("full_name"),
        "role": user.get("role", "user"),
        "is_approved": user.get("is_approved", False)
    }


# -----------------------------
# ✅ ADMIN HELPERS
# -----------------------------
def get_all_users():
    return list(users_collection.find({}, {"password": 0}))


def get_pending_users():
    return list(users_collection.find({"is_approved": False}, {"password": 0}))


def approve_user(username: str):
    result = users_collection.update_one(
        {"_id": username},
        {"$set": {"is_approved": True}}
    )
    return result.modified_count > 0


def deny_user(username: str):
    result = users_collection.update_one(
        {"_id": username}, {"$set": {"is_approved": False}}
    )
    return result.modified_count > 0


def update_user_role(username: str, role: str):
    result = users_collection.update_one(
        {"_id": username}, {"$set": {"role": role}}
    )
    return result.modified_count > 0

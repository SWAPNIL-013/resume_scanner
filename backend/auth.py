import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict

from passlib.context import CryptContext
import jwt

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)
USERS_FILE = os.path.join(DATA_DIR, "users.json")
JWT_SECRET = os.getenv("JWT_SECRET", "devsecret")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 3  # 3 hours

# Use pbkdf2_sha256 to avoid depending on native bcrypt binaries in dev environments.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def _load_users() -> Dict[str, Dict]:
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return {}


def _save_users(users: Dict[str, Dict]):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)


def register_user(username: str, password: str, full_name: Optional[str] = None) -> bool:
    users = _load_users()
    if username in users:
        return False
    hashed = pwd_context.hash(password)
    users[username] = {"username": username, "password": hashed, "full_name": full_name}
    _save_users(users)
    return True


def authenticate_user(username: str, password: str) -> Optional[Dict]:
    users = _load_users()
    user = users.get(username)
    if not user:
        return None
    if not pwd_context.verify(password, user["password"]):
        return None
    return {"username": user["username"], "full_name": user.get("full_name")}


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except Exception:
        return None


def get_user_from_token(token: str) -> Optional[Dict]:
    payload = decode_access_token(token)
    if not payload:
        return None
    username = payload.get("username")
    if not username:
        return None
    users = _load_users()
    user = users.get(username)
    if not user:
        return None
    return {"username": user["username"], "full_name": user.get("full_name")}
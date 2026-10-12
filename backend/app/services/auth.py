"""
Password hashing (bcrypt via passlib) and JWT-based session auth.

Stateless by design: a valid JWT is the session, so there's no sessions
table to keep in sync with Postgres/GCS backups.
"""
import os
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt


JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

_MAX_PASSWORD_BYTES = 72
 
 
def hash_password(plain_password: str) -> str:
    pw_bytes = plain_password.encode("utf-8")[:_MAX_PASSWORD_BYTES]
    return bcrypt.hashpw(pw_bytes, bcrypt.gensalt()).decode("utf-8")
 
 
def verify_password(plain_password: str, hashed_password: str) -> bool:
    pw_bytes = plain_password.encode("utf-8")[:_MAX_PASSWORD_BYTES]
    return bcrypt.checkpw(pw_bytes, hashed_password.encode("utf-8"))
 
 
def new_user_id() -> str:
    return uuid.uuid4().hex
 
 
def create_access_token(user_id: str, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {"sub": user_id, "email": email, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
 
 
def decode_access_token(token: str) -> dict | None:
    """Returns the payload dict if valid, None if expired/malformed/tampered."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None
 
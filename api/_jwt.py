import os
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from _db import get_db, to_dict, q

SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-change-in-prod-minimum-32-chars")
ALGORITHM = "HS256"
_bearer = HTTPBearer()


def create_token(user_id: int, email: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=24)
    return jwt.encode({"sub": str(user_id), "email": email, "exp": exp}, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(creds: HTTPAuthorizationCredentials = Depends(_bearer)) -> dict:
    try:
        payload = jwt.decode(creds.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail={"code": "TOKEN_EXPIRED", "message": "인증이 만료되었습니다"},
        )
    with get_db() as cur:
        cur.execute(q("SELECT id, email, team_id FROM users WHERE id = ?"), (user_id,))
        user = to_dict(cur.fetchone())
    if not user:
        raise HTTPException(
            status_code=401,
            detail={"code": "TOKEN_EXPIRED", "message": "인증이 만료되었습니다"},
        )
    return user

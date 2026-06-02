from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from supabase import create_client

from backend.config import SUPABASE_JWT_SECRET, SUPABASE_URL, SUPABASE_KEY

security = HTTPBearer()


def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token missing subject claim")

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    supabase.postgrest.auth(token)

    return {"user_id": user_id, "email": payload.get("email"), "payload": payload}

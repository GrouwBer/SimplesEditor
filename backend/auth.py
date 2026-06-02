from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from supabase import create_client

from backend.config import SUPABASE_URL, SUPABASE_KEY

router = APIRouter()


class SignUpRequest(BaseModel):
    email: str
    password: str


class SignInRequest(BaseModel):
    email: str
    password: str


@router.post("/signup")
async def signup(data: SignUpRequest):
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    try:
        response = supabase.auth.sign_up(
            {"email": data.email, "password": data.password}
        )
        return {
            "user": response.user.model_dump() if response.user else None,
            "session": response.session.model_dump() if response.session else None,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/signin")
async def signin(data: SignInRequest):
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    try:
        response = supabase.auth.sign_in_with_password(
            {"email": data.email, "password": data.password}
        )
        return {
            "user": response.user.model_dump() if response.user else None,
            "session": response.session.model_dump() if response.session else None,
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/signout")
async def signout():
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    try:
        supabase.auth.sign_out()
        return {"message": "Signed out successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

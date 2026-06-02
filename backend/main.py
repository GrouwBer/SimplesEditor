from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client

from backend.auth import router as auth_router
from backend.config import SUPABASE_URL, SUPABASE_KEY
from backend.dependencies import verify_jwt

app = FastAPI(title="SimplesEditor API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])


@app.get("/api/health")
async def health():
    supabase_ok = False
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        supabase_ok = True
    except Exception:
        pass

    return {
        "status": "ok" if supabase_ok else "degraded",
        "version": "0.1.0",
        "components": {
            "api": "up",
            "supabase": "up" if supabase_ok else "down",
        },
    }


@app.get("/api/protected", dependencies=[Depends(verify_jwt)])
async def protected_endpoint():
    return {"message": "You have access to this protected resource"}

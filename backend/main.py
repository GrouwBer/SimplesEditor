from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.auth import router as auth_router
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


@app.get("/api/protected", dependencies=[Depends(verify_jwt)])
async def protected_endpoint():
    return {"message": "You have access to this protected resource"}

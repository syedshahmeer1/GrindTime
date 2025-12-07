from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import sqlite3

from databaseauth import create_user, verify_user


app = FastAPI(
    title="GrindTime API",
    description="Backend API for workout & nutrition app",
    version="1.0.0",
)

ORIGINS_DEV = [
    "http://localhost:3000",
    "http://127.0.0.1:5500",
    "http://localhost:5173",
]

ORIGINS_PROD = [
    "https://grindtime1.netlify.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS_DEV + ORIGINS_PROD,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----- Request/Response models -----

class SignupRequest(BaseModel):
    email: EmailStr
    password: str


class SignupResponse(BaseModel):
    message: str
    user_id: int


class SigninRequest(BaseModel):
    email: EmailStr
    password: str


class SigninResponse(BaseModel):
    message: str
    user_id: int


@app.get("/")
async def health_check():
    return {"status": "ok", "message": "GrindTime API running"}


@app.post("/api/signup", response_model=SignupResponse, status_code=201)
async def signup(payload: SignupRequest):
    email = payload.email.strip().lower()
    password = payload.password

    if not password:
        raise HTTPException(status_code=400, detail="Password is required.")

    try:
        user_id = create_user(email, password)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Email already registered.")

    return SignupResponse(message="User created", user_id=user_id)


@app.post("/api/signin", response_model=SigninResponse)
async def signin(payload: SigninRequest):
    email = payload.email.strip().lower()
    password = payload.password

    if not password:
        raise HTTPException(status_code=400, detail="Password is required.")

    user = verify_user(email, password)
    if user is None:
        # Either email not found or password incorrect
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    return SigninResponse(
        message="Signed in",
        user_id=user["id"],
    )
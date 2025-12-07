from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt
from contextlib import asynccontextmanager
from typing import Optional
from datetime import datetime, timedelta
import sqlite3

from database import init_db
from databaseauth import create_user, verify_user

SECRET_KEY = "1d28e0b5c91fab3cd555e6c82805ec2ca97d01a51a75bdbf0cd31d1a42246132ff722552b649f568ed74ea207c03f595a1f04258e6bcccf46b6fd7690656400f"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # e.g. 7 days

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the database at startup (safe & persistent)
    init_db()
    yield
    

app = FastAPI(
    title="GrindTime API",
    description="Backend API for workout & nutrition app",
    version="1.0.0",
    lifespan=lifespan,
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

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt



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
    access_token: str
    token_type: str = "bearer"


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
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    # Create JWT token with user id and email
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user["id"]), "email": email},
        expires_delta=access_token_expires,
    )

    return SigninResponse(
        message="Signed in",
        user_id=user["id"],
        access_token=access_token,
        token_type="bearer",
    )
from fastapi import FastAPI, HTTPException, Depends, Header
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


def get_current_user_id(authorization: Optional[str] = Header(default=None)) -> int:
    """Extract and validate JWT from Authorization header and return user_id (sub)."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    token = parts[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(status_code=401, detail="Invalid token")
        return int(sub)
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")

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


class CalorieCalcSaveRequest(BaseModel):
    height_ft: int
    height_in: int
    weight_kg: float
    age_years: int
    sex: str
    activity_factor: float
    experience_level: str

    bmr_kcal: int
    maintenance_kcal: int
    bulk_kcal: int
    cut_kcal: int
    aggressive_cut_kcal: int
    protein_low_g: int
    protein_high_g: int


class CalorieCalcResult(BaseModel):
    created_at: str
    height_ft: Optional[int] = None
    height_in: Optional[int] = None
    weight_kg: Optional[float] = None
    age_years: Optional[int] = None
    sex: Optional[str] = None
    activity_factor: Optional[float] = None
    experience_level: Optional[str] = None

    bmr_kcal: Optional[int] = None
    maintenance_kcal: Optional[int] = None
    bulk_kcal: Optional[int] = None
    cut_kcal: Optional[int] = None
    aggressive_cut_kcal: Optional[int] = None
    protein_low_g: Optional[int] = None
    protein_high_g: Optional[int] = None


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


@app.post("/api/caloriecalc/save", status_code=201)
async def save_caloriecalc(payload: CalorieCalcSaveRequest, user_id: int = Depends(get_current_user_id)):
    """Save a set of calorie calculator results for the currently logged-in user."""
    with sqlite3.connect("grindtime.db") as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute(
            """
            INSERT INTO calorie_calc_results
            (user_id, height_ft, height_in, weight_kg, age_years, sex, activity_factor, experience_level,
             bmr_kcal, maintenance_kcal, bulk_kcal, cut_kcal, aggressive_cut_kcal, protein_low_g, protein_high_g)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                payload.height_ft,
                payload.height_in,
                payload.weight_kg,
                payload.age_years,
                payload.sex,
                payload.activity_factor,
                payload.experience_level,
                payload.bmr_kcal,
                payload.maintenance_kcal,
                payload.bulk_kcal,
                payload.cut_kcal,
                payload.aggressive_cut_kcal,
                payload.protein_low_g,
                payload.protein_high_g,
            ),
        )
        conn.commit()

    return {"message": "Saved"}


@app.get("/api/profile/caloriecalc", response_model=Optional[CalorieCalcResult])
async def get_latest_caloriecalc(user_id: int = Depends(get_current_user_id)):
    """Return the most recently saved calorie calculator results for the current user."""
    with sqlite3.connect("grindtime.db") as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        row = conn.execute(
            """
            SELECT created_at, height_ft, height_in, weight_kg, age_years, sex, activity_factor, experience_level,
                   bmr_kcal, maintenance_kcal, bulk_kcal, cut_kcal, aggressive_cut_kcal, protein_low_g, protein_high_g
            FROM calorie_calc_results
            WHERE user_id = ?
            ORDER BY datetime(created_at) DESC, id DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()

    if not row:
        return None
    return dict(row)
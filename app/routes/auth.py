from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import timedelta
from typing import Any

from app.database import get_database, settings
from app.schemas.user import UserCreate, UserResponse, Token, UserDb
from app.auth.security import get_password_hash, verify_password, create_access_token
from app.utils.rate_limit import limiter

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user: UserCreate, db: AsyncIOMotorDatabase = Depends(get_database)) -> Any:
    existing_user = await db["users"].find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = get_password_hash(user.password)
    new_user = UserDb(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        role="user"
    )
    
    result = await db["users"].insert_one(new_user.model_dump(by_alias=True, exclude={"id"}))
    created_user = await db["users"].find_one({"_id": result.inserted_id})
    
    # Create the response dictionary
    created_user["id"] = str(created_user.pop("_id"))
    return created_user

@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncIOMotorDatabase = Depends(get_database)) -> Any:
    # We will use the username field of the OAuth2 form to accept email
    user = await db["users"].find_one({"email": form_data.username})
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    if not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user["_id"]), "role": user.get("role", "user")},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

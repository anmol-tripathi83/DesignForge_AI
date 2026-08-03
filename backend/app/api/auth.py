from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse
from datetime import timedelta
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new user.
    - Checks if email already exists.
    - Hashes password.
    - Saves user to database.
    """
    # Check if user exists
    existing_user = await db.execute(select(User).where(User.email == user_data.email))
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash password and create user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        full_name=user_data.full_name
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user

@router.post("/login", response_model=UserResponse)
async def login(response: Response, login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    Login a user.
    - Validates credentials.
    - Creates JWT.
    - Sets JWT in an HTTP-Only cookie.
    """
    # Find user by email
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Create JWT token
    access_token = create_access_token(data={"sub": str(user.id)})

    # Set cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,          # Prevents JavaScript access
        secure=settings.ENVIRONMENT == "production",  # Send only over HTTPS in production
        samesite="lax",         # Protects against CSRF
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # seconds
        path="/"
    )

    return user

@router.get("/me", response_model=UserResponse)
async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Get the currently authenticated user.
    - Reads the access_token cookie.
    - Decodes JWT to get user ID.
    - Fetches user from database.
    """
    # Get token from cookie
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Decode token
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # Fetch user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return user

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(response: Response):
    """
    Logout the user by clearing the access_token cookie.
    """
    response.delete_cookie("access_token", path="/")
    return {"message": "Logged out successfully"}

# Dependency for protecting routes in other files
async def get_current_user_id(request: Request, db: AsyncSession = Depends(get_db)) -> str:
    """
    Helper dependency to get current user ID. Used by other routes (e.g., sessions).
    """
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return user_id
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
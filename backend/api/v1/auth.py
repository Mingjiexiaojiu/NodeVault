from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.deps import get_current_user
from backend.auth.jwt import create_access_token, get_password_hash, verify_password
from backend.database.session import get_db
from backend.models.namespace import Namespace
from backend.models.user import User
from backend.schemas.auth import TokenResponse, UserLogin, UserRegister, UserResponse
from backend.schemas.response import ApiResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)) -> ApiResponse:
    # Check for existing email or username
    existing = await db.execute(
        select(User).where(
            (User.email == payload.email) | (User.username == payload.username)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or username already registered",
        )

    user = User(
        email=payload.email,
        username=payload.username,
        hashed_password=get_password_hash(payload.password),
    )
    db.add(user)
    await db.flush()  # get user.id before creating namespace

    namespace = Namespace(
        slug=payload.username,
        display_name=payload.username,
        owner_id=user.id,
    )
    db.add(namespace)
    await db.commit()
    await db.refresh(user)
    return ApiResponse(data=UserResponse.model_validate(user).model_dump(), message="注册成功")


@router.post("/login", response_model=ApiResponse)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)) -> ApiResponse:
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(subject=str(user.id))
    return ApiResponse(data=TokenResponse(access_token=token).model_dump(), message="登录成功")


@router.get("/me", response_model=ApiResponse)
async def me(current_user: User = Depends(get_current_user)) -> ApiResponse:
    return ApiResponse(data=UserResponse.model_validate(current_user).model_dump())

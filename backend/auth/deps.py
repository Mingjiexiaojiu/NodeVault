import hashlib
import uuid

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, APIKeyHeader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.auth.jwt import decode_token
from backend.database.session import get_db
from backend.models.api_key import ApiKey
from backend.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)
apikey_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user(
    bearer: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    api_key_header: str | None = Security(apikey_header),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 提取 token 字符串
    token_str = bearer.credentials if bearer else None

    # Authorization: Bearer nvk_xxx 直接当 API Key 处理
    if token_str and token_str.startswith("nvk_"):
        api_key_header = token_str
        token_str = None

    # --- 方式一：JWT Bearer Token ---
    if token_str:
        try:
            payload = decode_token(token_str)
            user_id: str | None = payload.get("sub")
            if user_id is None:
                raise credentials_exception
        except ValueError:
            raise credentials_exception

        result = await db.execute(
            select(User).where(User.id == uuid.UUID(user_id)).options(selectinload(User.memberships))
        )
        user = result.scalar_one_or_none()
        if user is None or not user.is_active:
            raise credentials_exception
        return user

    # --- 方式二：API Key（X-API-Key 头或 Bearer nvk_xxx）---
    if api_key_header and api_key_header.startswith("nvk_"):
        key_hash = hashlib.sha256(api_key_header.encode()).hexdigest()
        result = await db.execute(
            select(ApiKey)
            .where(ApiKey.key_hash == key_hash, ApiKey.is_active.is_(True))
            .options(selectinload(ApiKey.owner).selectinload(User.memberships))
        )
        api_key = result.scalar_one_or_none()
        if api_key is None or not api_key.owner.is_active:
            raise credentials_exception

        # 更新最近使用时间（不阻塞主流程）
        from datetime import datetime
        from sqlalchemy import update
        await db.execute(
            update(ApiKey)
            .where(ApiKey.id == api_key.id)
            .values(last_used_at=datetime.utcnow())
        )
        await db.commit()
        return api_key.owner

    raise credentials_exception

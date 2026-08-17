import hashlib
import secrets
from datetime import timedelta

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.models import AuthSession
from app.timeutil import ensure_aware, now

__all__ = ["get_db", "require_token", "require_session", "hash_token"]


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def require_token(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少 Authorization 头",
        )
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization 格式应为 'Bearer <token>'",
        )
    if not secrets.compare_digest(token, settings.ACCESS_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token 无效",
        )


def require_session(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AuthSession:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少 Authorization 头",
        )
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization 格式应为 'Bearer <token>'",
        )
    token_hash = hash_token(token)
    session = db.execute(
        select(AuthSession).where(AuthSession.token_hash == token_hash)
    ).scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=401, detail="会话无效，请重新登录")
    now_dt = now()
    expires_at = ensure_aware(session.expires_at)
    if expires_at <= now_dt:
        db.delete(session)
        db.commit()
        raise HTTPException(status_code=401, detail="会话已过期，请重新登录")

    # 滑动续期：每天最多续一次，避免频繁写库
    if (now_dt - ensure_aware(session.last_seen_at)).total_seconds() > 24 * 3600:
        session.last_seen_at = now_dt
        session.expires_at = now_dt + timedelta(days=settings.SESSION_TTL_DAYS)
        db.commit()
    return session

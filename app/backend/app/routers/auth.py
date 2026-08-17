import secrets
import time
from collections import OrderedDict
from datetime import timedelta

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import delete as sa_delete
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.deps import hash_token, require_session
from app.models import AuthSession
from app.schemas.auth import LoginRequest, LoginResponse
from app.timeutil import now

router = APIRouter(tags=["auth"])

# 登录失败限流：ip -> deque(失败时间戳)。有界，超限淘汰最旧。
MAX_FAIL_ENTRIES = 5000
FAIL_WINDOW_SECONDS = 15 * 60
MAX_FAILS = 5
_fail_counts: "OrderedDict[str, list[float]]" = OrderedDict()


def _record_fail(ip: str) -> bool:
    """记录一次失败。返回 True 表示已被锁定。"""
    cutoff = time.time() - FAIL_WINDOW_SECONDS
    hits = [t for t in _fail_counts.get(ip, []) if t > cutoff]
    hits.append(time.time())
    _fail_counts[ip] = hits
    _fail_counts.move_to_end(ip)
    if len(_fail_counts) > MAX_FAIL_ENTRIES:
        _fail_counts.popitem(last=False)
    return len(hits) >= MAX_FAILS


def reset_fail_counts() -> None:
    """清理超过时间窗的失败记录（保留窗口内的计数）。"""
    cutoff = time.time() - FAIL_WINDOW_SECONDS
    for ip in list(_fail_counts):
        _fail_counts[ip] = [t for t in _fail_counts[ip] if t > cutoff]
        if not _fail_counts[ip]:
            del _fail_counts[ip]


def clear_fail_counts() -> None:
    """清空全部登录失败计数（仅测试/运维用）。"""
    _fail_counts.clear()


def is_locked(ip: str) -> bool:
    cutoff = time.time() - FAIL_WINDOW_SECONDS
    return len([t for t in _fail_counts.get(ip, []) if t > cutoff]) >= MAX_FAILS


@router.post("/auth/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user_agent: str | None = Header(default=None),
    x_forwarded_for: str | None = Header(default=None),
):
    ip = (x_forwarded_for or "unknown").split(",")[0].strip() or "unknown"
    if is_locked(ip):
        raise HTTPException(status_code=429, detail="尝试过于频繁，请 15 分钟后再试")

    username_ok = secrets.compare_digest(payload.username, settings.LOGIN_USERNAME)
    password_ok = bool(settings.LOGIN_PASSWORD) and secrets.compare_digest(
        payload.password, settings.LOGIN_PASSWORD
    )
    if not (username_ok and password_ok):
        _record_fail(ip)
        raise HTTPException(status_code=401, detail="账号或密码错误")

    token = secrets.token_hex(32)
    now_dt = now()
    session = AuthSession(
        token_hash=hash_token(token),
        ip=ip[:45],
        user_agent=(user_agent or "")[:255],
        created_at=now_dt,
        expires_at=now_dt + timedelta(days=settings.SESSION_TTL_DAYS),
        last_seen_at=now_dt,
    )
    db.add(session)
    db.commit()
    return LoginResponse(token=token)


@router.post("/auth/logout")
def logout(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token:
            db.execute(
                sa_delete(AuthSession).where(AuthSession.token_hash == hash_token(token))
            )
            db.commit()
    return {"ok": True}


@router.get("/auth/me")
def me(_: AuthSession = Depends(require_session)):
    return {"ok": True}

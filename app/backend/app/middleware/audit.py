"""写操作审计中间件：记录所有非 GET /api 请求。"""

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.database import SessionLocal
from app.deps import hash_token
from app.models import AuditLog, AuthSession

logger = logging.getLogger(__name__)

WRITE_METHODS = {"POST", "PATCH", "PUT", "DELETE"}


class AuditMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, session_factory=SessionLocal):
        super().__init__(app)
        self._session_factory = session_factory

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        if request.method not in WRITE_METHODS:
            return response
        uri = request.url.path
        if not uri.startswith("/api/v1") or uri == "/api/v1/auth/login":
            return response
        try:
            self._record(request, response.status_code)
        except Exception:  # noqa: BLE001
            logger.exception("audit log write failed")
        return response

    def _record(self, request: Request, status_code: int) -> None:
        authorization = request.headers.get("authorization", "")
        session_id = None
        if authorization.lower().startswith("bearer "):
            token = authorization[7:]
            if token:
                db = self._session_factory()
                try:
                    session = (
                        db.query(AuthSession)
                        .filter(AuthSession.token_hash == hash_token(token))
                        .first()
                    )
                    session_id = session.id if session else None
                finally:
                    db.close()
        user_agent = (request.headers.get("user-agent") or "")[:255]
        ip = (request.headers.get("x-forwarded-for") or "unknown").split(",")[0].strip()[:45]
        request_id = (request.headers.get("x-request-id") or "")[:64]
        db = self._session_factory()
        try:
            db.add(
                AuditLog(
                    ip=ip,
                    user_agent=user_agent or None,
                    method=request.method,
                    uri=request.url.path[:255],
                    status=status_code,
                    session_id=session_id,
                    request_id=request_id or None,
                )
            )
            db.commit()
        finally:
            db.close()

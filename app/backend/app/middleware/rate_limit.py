"""API 通用限流中间件：每 IP 每分钟请求数上限，防脚本刷接口。

内存有界：最多保留 MAX_ENTRIES 个 IP 计数，超限淘汰最旧；窗口过期自动清理。
"""

import logging
import time
from collections import OrderedDict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

RATE_LIMIT_PER_MINUTE = 120
MAX_ENTRIES = 5000
WINDOW_SECONDS = 60

_buckets: "OrderedDict[str, tuple[int, float]]" = OrderedDict()  # ip -> (count, window_start)


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def clear_rate_limits() -> None:
    _buckets.clear()


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if not path.startswith("/api/v1") or path in ("/api/v1/health", "/api/v1/auth/login"):
            return await call_next(request)

        ip = _client_ip(request)
        now = time.time()
        count, start = _buckets.get(ip, (0, now))
        if now - start >= WINDOW_SECONDS:
            count, start = 0, now
        count += 1
        if count > RATE_LIMIT_PER_MINUTE:
            return JSONResponse(
                status_code=429,
                content={"detail": "请求过于频繁，请稍后再试"},
            )
        _buckets[ip] = (count, start)
        _buckets.move_to_end(ip)
        if len(_buckets) > MAX_ENTRIES:
            _buckets.popitem(last=False)

        response: Response = await call_next(request)
        return response

"""FastAPI 入口。"""

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.deps import require_session
from app.middleware.audit import AuditMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_context import RequestContextMiddleware
from app.routers import auth, backup, export, lessons, settings as settings_router, stats, students, templates
from app.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
logger = logging.getLogger("app")

settings_cfg = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="课表",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(AuditMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestContextMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings_cfg.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health")
def health():
    return {"status": "ok"}


api_prefix = "/api/v1"
auth_deps = [Depends(require_session)]
app.include_router(auth.router, prefix=api_prefix)
app.include_router(settings_router.router, prefix=api_prefix, dependencies=auth_deps)
app.include_router(students.router, prefix=api_prefix, dependencies=auth_deps)
app.include_router(templates.router, prefix=api_prefix, dependencies=auth_deps)
app.include_router(lessons.router, prefix=api_prefix, dependencies=auth_deps)
app.include_router(stats.router, prefix=api_prefix, dependencies=auth_deps)
app.include_router(export.router, prefix=api_prefix, dependencies=auth_deps)
app.include_router(backup.router, prefix=api_prefix, dependencies=auth_deps)

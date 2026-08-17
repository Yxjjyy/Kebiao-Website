"""APScheduler 后台任务。"""

import logging
from datetime import timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.middleware.rate_limit import clear_rate_limits
from app.database import SessionLocal
from app.config import get_settings
from app.models import AuditLog, AuthSession
from app.routers.auth import reset_fail_counts
from app.services import lesson_service
from app.timeutil import now

logger = logging.getLogger(__name__)
scheduler: BackgroundScheduler | None = None


def _auto_complete_job() -> None:
    db = SessionLocal()
    try:
        n = lesson_service.auto_complete_past_lessons(db)
        logger.info("auto_complete_past_lessons: %d 节课转为已完成", n)
    finally:
        db.close()


def _roll_forward_job() -> None:
    db = SessionLocal()
    try:
        n = lesson_service.roll_forward_all_templates(db)
        logger.info("roll_forward_all_templates: 新增 %d 节课", n)
    finally:
        db.close()


def _cleanup_security_job() -> None:
    """每日清理：过期会话、90 天前审计日志、登录失败计数。"""
    db = SessionLocal()
    try:
        now_naive = now().replace(tzinfo=None)
        expired = (
            db.query(AuthSession).filter(AuthSession.expires_at <= now_naive).delete()
        )
        old_audit = (
            db.query(AuditLog)
            .filter(AuditLog.created_at < now_naive - timedelta(days=90))
            .delete()
        )
        db.commit()
        logger.info("cleanup_security: 过期会话 %d 条, 旧审计 %d 条", expired, old_audit)
    finally:
        db.close()
    reset_fail_counts()
    clear_rate_limits()


def start_scheduler() -> None:
    global scheduler
    if scheduler is not None:
        return
    timezone_name = get_settings().TIMEZONE
    scheduler = BackgroundScheduler(timezone=timezone_name)
    scheduler.add_job(
        _auto_complete_job,
        CronTrigger(hour=0, minute=5, timezone=timezone_name),
        id="auto_complete_past_lessons",
        replace_existing=True,
    )
    scheduler.add_job(
        _roll_forward_job,
        CronTrigger(hour=0, minute=10, timezone=timezone_name),
        id="roll_forward_all_templates",
        replace_existing=True,
    )
    scheduler.add_job(
        _cleanup_security_job,
        CronTrigger(hour=3, minute=20, timezone=timezone_name),
        id="cleanup_security",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("scheduler 已启动（00:05 自动完成、00:10 滚动生成、03:20 安全清理）")


def stop_scheduler() -> None:
    global scheduler
    if scheduler is not None:
        scheduler.shutdown(wait=False)
        scheduler = None

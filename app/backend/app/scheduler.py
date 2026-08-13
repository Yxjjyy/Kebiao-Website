"""APScheduler 后台任务。"""

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.database import SessionLocal
from app.config import get_settings
from app.services import lesson_service

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
    scheduler.start()
    logger.info("scheduler 已启动（00:05 自动完成、00:10 滚动生成）")


def stop_scheduler() -> None:
    global scheduler
    if scheduler is not None:
        scheduler.shutdown(wait=False)
        scheduler = None

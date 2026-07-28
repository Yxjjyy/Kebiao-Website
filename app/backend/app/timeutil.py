"""时间工具：所有日期/时间操作统一走 Asia/Shanghai。"""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.config import get_settings

_settings = get_settings()
TZ = ZoneInfo(_settings.TIMEZONE)


def now() -> datetime:
    return datetime.now(TZ)


def today() -> date:
    return now().date()


def parse_date(s: str) -> date:
    return date.fromisoformat(s)


def parse_time(s: str) -> time:
    return time.fromisoformat(s)


def time_to_minutes(t: time | str) -> int:
    if isinstance(t, str):
        t = parse_time(t)
    return t.hour * 60 + t.minute


def minutes_to_time(m: int) -> time:
    return time(hour=m // 60, minute=m % 60)


def lesson_end_minutes(start_time: str, duration_hours: float) -> int:
    return time_to_minutes(start_time) + int(duration_hours * 60)


def overlaps(a_start_min: int, a_end_min: int, b_start_min: int, b_end_min: int) -> bool:
    """两个时段是否重叠（左闭右开）。"""
    return not (a_end_min <= b_start_min or b_end_min <= a_start_min)


def week_start(d: date) -> date:
    """ISO 周一为周首日。"""
    return d - timedelta(days=d.weekday())


def week_end(d: date) -> date:
    return week_start(d) + timedelta(days=6)


def month_start(d: date) -> date:
    return d.replace(day=1)


def month_end(d: date) -> date:
    nxt = (d.replace(day=28) + timedelta(days=4)).replace(day=1)
    return nxt - timedelta(days=1)


def add_days(d: date, n: int) -> date:
    return d + timedelta(days=n)


def iter_dates_for_weekday(
    start: date,
    end: date,
    weekday: int,
) -> list[date]:
    """返回 [start, end] 区间内所有指定星期几（0=周一）的日期。"""
    if start > end:
        return []
    offset = (weekday - start.weekday()) % 7
    first = start + timedelta(days=offset)
    out: list[date] = []
    cur = first
    while cur <= end:
        out.append(cur)
        cur += timedelta(days=7)
    return out

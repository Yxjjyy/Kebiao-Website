"""统计聚合服务：今日总结、区间趋势、学生排行、同期对比。"""

from datetime import date, timedelta

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Lesson, Student
from app.schemas.lesson import LessonOut, StudentLite
from app.schemas.stats import (
    ComparisonStats,
    LeaveItem,
    RangeBucket,
    RangeStats,
    StudentStatsRow,
    TodayStats,
)
from app.timeutil import (
    month_end,
    month_start,
    today,
    week_end,
    week_start,
)

ACTIVE_STATUSES = ("待上", "已完成")
EARNED_STATUSES = ("已完成",)


def today_summary(db: Session) -> TodayStats:
    today_ = today()
    rows = (
        db.execute(
            select(Lesson)
            .options(selectinload(Lesson.student))
            .where(Lesson.date == today_)
            .order_by(Lesson.start_time)
        )
        .scalars()
        .all()
    )
    expected = sum(r.price for r in rows if r.status in ACTIVE_STATUSES)
    earned = sum(r.price for r in rows if r.status == "已完成")
    hours = sum(r.duration_hours for r in rows if r.status in ACTIVE_STATUSES)
    return TodayStats(
        date=today_,
        total_lessons=sum(1 for r in rows if r.status in ACTIVE_STATUSES),
        expected_income=float(expected),
        earned_income=float(earned),
        total_hours=float(hours),
        lessons=[
            LessonOut(
                **{
                    k: getattr(r, k)
                    for k in (
                        "id",
                        "student_id",
                        "template_id",
                        "date",
                        "start_time",
                        "duration_hours",
                        "status",
                        "price",
                        "note",
                        "rescheduled_from_id",
                        "rescheduled_to_id",
                        "created_at",
                        "updated_at",
                    )
                },
                student=StudentLite.model_validate(r.student) if r.student else None,
            )
            for r in rows
        ],
    )


def _bucket_key(d: date, granularity: str) -> str:
    if granularity == "day":
        return d.isoformat()
    if granularity == "week":
        return week_start(d).isoformat()
    if granularity == "month":
        return d.strftime("%Y-%m")
    raise ValueError("granularity 必须为 day/week/month")


def range_stats(
    db: Session,
    *,
    from_date: date,
    to_date: date,
    granularity: str = "day",
) -> RangeStats:
    rows = db.execute(
        select(Lesson).where(
            Lesson.date >= from_date,
            Lesson.date <= to_date,
            Lesson.status.in_(ACTIVE_STATUSES),
        )
    ).scalars().all()

    completed = [r for r in rows if r.status == "已完成"]

    buckets: dict[str, dict] = {}
    for r in completed:
        key = _bucket_key(r.date, granularity)
        b = buckets.setdefault(
            key, {"income": 0.0, "hours": 0.0, "lesson_count": 0}
        )
        b["income"] += r.price
    for r in rows:
        key = _bucket_key(r.date, granularity)
        b = buckets.setdefault(
            key, {"income": 0.0, "hours": 0.0, "lesson_count": 0}
        )
        b["hours"] += r.duration_hours
        b["lesson_count"] += 1

    bucket_list = sorted(
        [
            RangeBucket(
                bucket=k,
                income=float(v["income"]),
                hours=float(v["hours"]),
                lesson_count=int(v["lesson_count"]),
            )
            for k, v in buckets.items()
        ],
        key=lambda x: x.bucket,
    )

    return RangeStats(
        from_date=from_date,
        to_date=to_date,
        granularity=granularity,
        total_income=float(sum(r.price for r in completed)),
        total_hours=float(sum(r.duration_hours for r in rows)),
        total_lessons=len(rows),
        buckets=bucket_list,
    )


def student_ranking(
    db: Session, *, from_date: date, to_date: date
) -> list[StudentStatsRow]:
    stmt = (
        select(
            Student.id,
            Student.name,
            Student.color,
            func.coalesce(
                func.sum(
                    case(
                        (Lesson.status.in_(ACTIVE_STATUSES), 1),
                        else_=0,
                    )
                ),
                0,
            ).label("lesson_count"),
            func.coalesce(
                func.sum(
                    case(
                        (Lesson.status.in_(ACTIVE_STATUSES), Lesson.duration_hours),
                        else_=0.0,
                    )
                ),
                0.0,
            ).label("total_hours"),
            func.coalesce(
                func.sum(
                    case(
                        (Lesson.status.in_(EARNED_STATUSES), Lesson.price),
                        else_=0.0,
                    )
                ),
                0.0,
            ).label("total_income"),
            func.coalesce(
                func.sum(case((Lesson.status == "请假", 1), else_=0)), 0
            ).label("leave_count"),
            func.coalesce(
                func.sum(case((Lesson.status == "已调课", 1), else_=0)), 0
            ).label("reschedule_count"),
        )
        .select_from(Student)
        .join(
            Lesson,
            (Lesson.student_id == Student.id)
            & (Lesson.date >= from_date)
            & (Lesson.date <= to_date),
            isouter=True,
        )
        .where(Student.archived == 0)
        .group_by(Student.id, Student.name, Student.color)
        .order_by(func.coalesce(
            func.sum(
                case(
                    (Lesson.status.in_(EARNED_STATUSES), Lesson.price), else_=0.0
                )
            ),
            0.0,
        ).desc())
    )
    rows = db.execute(stmt).all()
    return [
        StudentStatsRow(
            student_id=r.id,
            name=r.name,
            color=r.color,
            lesson_count=int(r.lesson_count),
            total_hours=float(r.total_hours),
            total_income=float(r.total_income),
            leave_count=int(r.leave_count),
            reschedule_count=int(r.reschedule_count),
        )
        for r in rows
    ]


def leave_list(
    db: Session, *, from_date: date, to_date: date
) -> list[LeaveItem]:
    rows = (
        db.execute(
            select(Lesson)
            .options(selectinload(Lesson.student))
            .where(
                Lesson.date >= from_date,
                Lesson.date <= to_date,
                Lesson.status.in_(("请假", "已调课")),
            )
            .order_by(Lesson.date.desc(), Lesson.start_time)
        )
        .scalars()
        .all()
    )
    return [
        LeaveItem(
            id=r.id,
            student_id=r.student_id,
            student_name=r.student.name if r.student else "",
            date=r.date,
            start_time=r.start_time,
            duration_hours=r.duration_hours,
            status=r.status,
            note=r.note,
        )
        for r in rows
    ]


def _sum_in_range(db: Session, start: date, end: date, statuses: tuple[str, ...] = ACTIVE_STATUSES) -> tuple[float, float, int]:
    rows = db.execute(
        select(Lesson).where(
            Lesson.date >= start,
            Lesson.date <= end,
            Lesson.status.in_(statuses),
        )
    ).scalars().all()
    income = float(sum(r.price for r in rows))
    hours = float(sum(r.duration_hours for r in rows))
    return income, hours, len(rows)


def _growth_pct(cur: float, prev: float) -> float | None:
    if prev == 0:
        return None
    return (cur - prev) / prev * 100.0


def comparison(db: Session, period: str = "week") -> ComparisonStats:
    today_ = today()
    if period == "week":
        cur_start = week_start(today_)
        cur_end = today_
        days_elapsed = (today_ - cur_start).days
        prev_start = cur_start - timedelta(days=7)
        prev_end = prev_start + timedelta(days=days_elapsed)
    elif period == "month":
        cur_start = month_start(today_)
        cur_end = today_
        days_elapsed = (today_ - cur_start).days
        prev_month_today = cur_start - timedelta(days=1)
        prev_start = month_start(prev_month_today)
        prev_end = prev_start + timedelta(days=days_elapsed)
        # 若上月没有这么多天，截到月末
        prev_end = min(prev_end, month_end(prev_month_today))
    else:
        raise ValueError("period 必须为 week/month")

    cur_income, cur_hours, cur_lessons = _sum_in_range(db, cur_start, cur_end)
    prev_income, prev_hours, prev_lessons = _sum_in_range(db, prev_start, prev_end)
    cur_earned = _sum_in_range(db, cur_start, cur_end, EARNED_STATUSES)[0]
    prev_earned = _sum_in_range(db, prev_start, prev_end, EARNED_STATUSES)[0]

    return ComparisonStats(
        period=period,
        current_income=cur_earned,
        previous_income=prev_earned,
        income_growth_pct=_growth_pct(cur_earned, prev_earned),
        current_hours=cur_hours,
        previous_hours=prev_hours,
        hours_growth_pct=_growth_pct(cur_hours, prev_hours),
        current_lessons=cur_lessons,
        previous_lessons=prev_lessons,
    )

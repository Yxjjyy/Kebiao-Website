"""课时实例服务：生成、冲突检测、调课、状态变更。"""

from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.orm import Session, selectinload

from app.models import Lesson, ScheduleTemplate, Settings, Student
from app.schemas.lesson import LessonCreate, LessonReschedule, LessonUpdate
from app.timeutil import (
    iter_dates_for_weekday,
    lesson_end_minutes,
    now,
    overlaps,
    time_to_minutes,
    today,
)


# ---------------------------- 冲突检测 ----------------------------


def find_conflicts(
    db: Session,
    *,
    on_date: date,
    start_time: str,
    duration_hours: float,
    exclude_lesson_id: int | None = None,
) -> list[Lesson]:
    new_start = time_to_minutes(start_time)
    new_end = new_start + int(duration_hours * 60)
    stmt = (
        select(Lesson)
        .options(selectinload(Lesson.student))
        .where(
            Lesson.date == on_date,
            Lesson.status.in_(("待上", "已完成")),
        )
    )
    if exclude_lesson_id is not None:
        stmt = stmt.where(Lesson.id != exclude_lesson_id)
    candidates = db.execute(stmt).scalars().all()
    conflicts: list[Lesson] = []
    for c in candidates:
        c_start = time_to_minutes(c.start_time)
        c_end = c_start + int(c.duration_hours * 60)
        if overlaps(new_start, new_end, c_start, c_end):
            conflicts.append(c)
    return conflicts


def raise_if_conflict(
    db: Session,
    *,
    on_date: date,
    start_time: str,
    duration_hours: float,
    exclude_lesson_id: int | None = None,
) -> None:
    conflicts = find_conflicts(
        db,
        on_date=on_date,
        start_time=start_time,
        duration_hours=duration_hours,
        exclude_lesson_id=exclude_lesson_id,
    )
    if conflicts:
        detail = [
            {
                "id": c.id,
                "student_id": c.student_id,
                "student_name": c.student.name if c.student else "",
                "start_time": c.start_time,
                "duration_hours": c.duration_hours,
                "date": c.date.isoformat(),
            }
            for c in conflicts
        ]
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "time_conflict", "conflicts": detail},
        )


# ---------------------------- 实例生成 ----------------------------


def _get_horizon(db: Session) -> date:
    s = db.get(Settings, 1)
    weeks = s.generate_weeks_ahead if (s and s.generate_weeks_ahead) else 12
    return today() + timedelta(weeks=weeks)


def materialize_template(
    db: Session,
    template: ScheduleTemplate,
    *,
    from_date: date | None = None,
    to_date: date | None = None,
) -> int:
    """为模板生成 lesson 实例。返回新增数量。支持 repeat_interval 隔周。"""
    student = db.get(Student, template.student_id)
    if not student:
        return 0
    start = max(
        from_date or template.effective_from,
        template.effective_from,
    )
    end = min(
        to_date or _get_horizon(db),
        template.effective_to or (to_date or _get_horizon(db)),
    )
    if start > end:
        return 0
    target_dates = iter_dates_for_weekday(start, end, template.day_of_week)
    if not target_dates:
        return 0

    # repeat_interval 隔周过滤：以 effective_from 所在周为基准
    interval = max(1, template.repeat_interval)
    if interval > 1:
        base_week_start = template.effective_from - timedelta(days=template.effective_from.weekday())
        filtered: list[date] = []
        for d in target_dates:
            dws = d - timedelta(days=d.weekday())
            week_num = (dws - base_week_start).days // 7
            if week_num % interval == 0:
                filtered.append(d)
        target_dates = filtered

    existing_dates = set(
        db.execute(
            select(Lesson.date).where(
                Lesson.template_id == template.id,
                Lesson.date.in_(target_dates),
            )
        )
        .scalars()
        .all()
    )

    created = 0
    for d in target_dates:
        if d in existing_dates:
            continue
        # 若该时段有冲突（来自其他模板/临时课），跳过
        conflicts = find_conflicts(
            db,
            on_date=d,
            start_time=template.start_time,
            duration_hours=template.duration_hours,
        )
        if conflicts:
            continue
        lesson = Lesson(
            student_id=template.student_id,
            template_id=template.id,
            date=d,
            start_time=template.start_time,
            duration_hours=template.duration_hours,
            status="待上",
            price=student.hourly_rate * template.duration_hours,
        )
        db.add(lesson)
        created += 1
    db.commit()
    return created


def regenerate_template_future(
    db: Session,
    template: ScheduleTemplate,
    *,
    from_date: date,
) -> int:
    """删除该模板从 from_date 起所有未上的 lesson，再重新生成。"""
    db.execute(
        Lesson.__table__.delete().where(
            and_(
                Lesson.template_id == template.id,
                Lesson.date >= from_date,
                Lesson.status == "待上",
            )
        )
    )
    db.commit()
    return materialize_template(db, template, from_date=from_date)


def roll_forward_all_templates(db: Session) -> int:
    """每日定时任务：把所有活跃模板生成范围推进到 horizon。"""
    horizon = _get_horizon(db)
    today_ = today()
    total = 0
    templates = db.execute(select(ScheduleTemplate)).scalars().all()
    for t in templates:
        if t.effective_to and t.effective_to < today_:
            continue
        total += materialize_template(db, t, from_date=today_, to_date=horizon)
    return total


def auto_complete_past_lessons(db: Session) -> int:
    """每日 00:05：把过期的 待上 自动转 已完成。"""
    today_ = today()
    current_minutes = time_to_minutes(now().time())
    rows = db.execute(
        select(Lesson).where(
            Lesson.status == "待上",
            Lesson.date <= today_,
        )
    ).scalars().all()
    completed: list[Lesson] = []
    for ls in rows:
        end_min = lesson_end_minutes(ls.start_time, ls.duration_hours)
        if ls.date < today_:
            if end_min > 1440:
                # 跨午夜课程（如23:00-01:00），折算到今天判断是否已结束
                if end_min - 1440 >= current_minutes:
                    continue
            completed.append(ls)
        elif end_min < current_minutes:
            completed.append(ls)
    for ls in completed:
        ls.status = "已完成"
    db.commit()
    return len(completed)


# ---------------------------- lesson CRUD ----------------------------


def list_lessons(
    db: Session,
    *,
    from_date: date,
    to_date: date,
    student_id: int | None = None,
) -> list[Lesson]:
    stmt = (
        select(Lesson)
        .options(selectinload(Lesson.student))
        .where(Lesson.date >= from_date, Lesson.date <= to_date)
    )
    if student_id is not None:
        stmt = stmt.where(Lesson.student_id == student_id)
    stmt = stmt.order_by(Lesson.date, Lesson.start_time)
    return list(db.execute(stmt).scalars().all())


def get_lesson(db: Session, lesson_id: int) -> Lesson:
    ls = db.get(Lesson, lesson_id)
    if not ls:
        raise HTTPException(status_code=404, detail="课时不存在")
    return ls


def create_lesson(db: Session, payload: LessonCreate) -> Lesson:
    student = db.get(Student, payload.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    raise_if_conflict(
        db,
        on_date=payload.date,
        start_time=payload.start_time,
        duration_hours=payload.duration_hours,
    )
    ls = Lesson(
        student_id=payload.student_id,
        template_id=None,
        date=payload.date,
        start_time=payload.start_time,
        duration_hours=payload.duration_hours,
        status="待上",
        price=student.hourly_rate * payload.duration_hours,
        note=payload.note,
    )
    db.add(ls)
    db.commit()
    db.refresh(ls)
    return ls


def update_lesson(db: Session, lesson_id: int, payload: LessonUpdate) -> Lesson:
    ls = get_lesson(db, lesson_id)
    data = payload.model_dump(exclude_unset=True)

    new_date = data.get("date", ls.date)
    new_time = data.get("start_time", ls.start_time)
    new_dur = data.get("duration_hours", ls.duration_hours)
    new_status = data.get("status", ls.status)

    # 仅当依然处于 待上/已完成 状态、且时段或日期有改动，才检测冲突
    time_changed = (
        new_date != ls.date or new_time != ls.start_time or new_dur != ls.duration_hours
    )
    if new_status in ("待上", "已完成") and time_changed:
        raise_if_conflict(
            db,
            on_date=new_date,
            start_time=new_time,
            duration_hours=new_dur,
            exclude_lesson_id=ls.id,
        )

    # 若从"已调课"改为"待上"，清理调课引用
    if ls.status == "已调课" and new_status == "待上":
        if ls.rescheduled_to_id:
            new_lesson = db.get(Lesson, ls.rescheduled_to_id)
            if new_lesson:
                new_lesson.rescheduled_from_id = None
        data["rescheduled_to_id"] = None

    for k, v in data.items():
        setattr(ls, k, v)

    # 若改了时长，按学生当前单价重新计算 price
    if "duration_hours" in data:
        student = db.get(Student, ls.student_id)
        if student:
            ls.price = student.hourly_rate * ls.duration_hours

    db.commit()
    db.refresh(ls)
    return ls


def reschedule_lesson(
    db: Session, lesson_id: int, payload: LessonReschedule
) -> tuple[Lesson, Lesson]:
    """返回 (旧 lesson 已标已调课, 新 lesson)。"""
    old = get_lesson(db, lesson_id)
    if old.status in ("请假", "已调课"):
        raise HTTPException(status_code=400, detail=f"该课时状态为「{old.status}」，无法调课")
    student = db.get(Student, old.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    new_dur = payload.new_duration_hours or old.duration_hours
    raise_if_conflict(
        db,
        on_date=payload.new_date,
        start_time=payload.new_start_time,
        duration_hours=new_dur,
        exclude_lesson_id=old.id,
    )

    new_lesson = Lesson(
        student_id=old.student_id,
        template_id=old.template_id,
        date=payload.new_date,
        start_time=payload.new_start_time,
        duration_hours=new_dur,
        status="待上",
        price=student.hourly_rate * new_dur,
        note=payload.note,
        rescheduled_from_id=old.id,
    )
    db.add(new_lesson)
    db.flush()
    old.status = "已调课"
    old.rescheduled_to_id = new_lesson.id
    db.commit()
    db.refresh(old)
    db.refresh(new_lesson)
    return old, new_lesson


def cancel_lesson(db: Session, lesson_id: int, note: str | None = None) -> Lesson:
    ls = get_lesson(db, lesson_id)
    if ls.status == "已调课":
        raise HTTPException(status_code=400, detail="已调课的课时不能直接请假，请先处理调课记录")
    ls.status = "请假"
    if note is not None:
        ls.note = note
    db.commit()
    db.refresh(ls)
    return ls


def restore_lesson(db: Session, lesson_id: int) -> Lesson:
    ls = get_lesson(db, lesson_id)
    if ls.status not in ("请假", "已调课"):
        return ls
    # 冲突检测（恢复成 待上 时同样要校验）
    raise_if_conflict(
        db,
        on_date=ls.date,
        start_time=ls.start_time,
        duration_hours=ls.duration_hours,
        exclude_lesson_id=ls.id,
    )
    # 若从"已调课"恢复，清理新课时对旧课的反向引用
    if ls.status == "已调课" and ls.rescheduled_to_id:
        new_lesson = db.get(Lesson, ls.rescheduled_to_id)
        if new_lesson:
            new_lesson.rescheduled_from_id = None
    ls.status = "待上"
    ls.rescheduled_to_id = None
    db.commit()
    db.refresh(ls)
    return ls


def delete_lesson(db: Session, lesson_id: int) -> None:
    ls = get_lesson(db, lesson_id)
    db.delete(ls)
    db.commit()


def bulk_action(
    db: Session,
    *,
    lesson_ids: list[int],
    action: str,
    note: str | None = None,
) -> dict[str, int]:
    affected = 0
    for lesson_id in lesson_ids:
        if action == "delete":
            ls = get_lesson(db, lesson_id)
            db.delete(ls)
            affected += 1
            continue
        if action == "complete":
            ls = update_lesson(db, lesson_id, LessonUpdate(status="已完成"))
        elif action == "cancel":
            ls = cancel_lesson(db, lesson_id, note)
        elif action == "restore":
            ls = get_lesson(db, lesson_id)
            if ls.status in ("请假", "已调课"):
                ls = restore_lesson(db, lesson_id)
            else:
                continue
        else:
            raise HTTPException(status_code=400, detail="不支持的批量操作")
        affected += 1
    db.commit()
    return {"affected": affected}

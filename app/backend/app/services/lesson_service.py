"""课时实例服务：生成、冲突检测、调课、状态变更。"""

from datetime import date, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.orm import Session, selectinload

from app.models import Lesson, ScheduleTemplate, Settings, Student, TemplateLessonTombstone
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
    new_start = datetime.combine(on_date, datetime.strptime(start_time, "%H:%M").time())
    new_end = new_start + timedelta(hours=duration_hours)
    stmt = (
        select(Lesson)
        .options(selectinload(Lesson.student))
        .where(
            Lesson.date >= on_date - timedelta(days=1),
            Lesson.date <= on_date + timedelta(days=1),
            Lesson.status.in_(("待上", "已完成")),
        )
    )
    if exclude_lesson_id is not None:
        stmt = stmt.where(Lesson.id != exclude_lesson_id)
    candidates = db.execute(stmt).scalars().all()
    conflicts: list[Lesson] = []
    for c in candidates:
        c_start = datetime.combine(c.date, datetime.strptime(c.start_time, "%H:%M").time())
        c_end = c_start + timedelta(hours=c.duration_hours)
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
    commit: bool = True,
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
    # 用户删除过的日期不重建（墓碑机制）
    tombstoned_dates = set(
        db.execute(
            select(TemplateLessonTombstone.date).where(
                TemplateLessonTombstone.template_id == template.id,
                TemplateLessonTombstone.date.in_(target_dates),
            )
        )
        .scalars()
        .all()
    )

    created = 0
    for d in target_dates:
        if d in existing_dates or d in tombstoned_dates:
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
    if commit:
        db.commit()
    return created


def regenerate_template_future(
    db: Session,
    template: ScheduleTemplate,
    *,
    from_date: date,
    commit: bool = True,
) -> int:
    """删除该模板从 from_date 起所有未上的 lesson（排除调课生成的新课时），再重新生成。"""
    db.execute(
        Lesson.__table__.delete().where(
            and_(
                Lesson.template_id == template.id,
                Lesson.date >= from_date,
                Lesson.status == "待上",
                Lesson.rescheduled_from_id.is_(None),
            )
        )
    )
    if commit:
        db.commit()
    return materialize_template(db, template, from_date=from_date, commit=commit)


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
    """每日 00:05：把已经结束（含跨午夜）的 待上 课程自动转 已完成。"""
    now_ = now()
    rows = db.execute(
        select(Lesson).where(
            Lesson.status == "待上",
            Lesson.date <= now_.date(),
        )
    ).scalars().all()
    completed: list[Lesson] = []
    for ls in rows:
        start_dt = datetime.combine(ls.date, datetime.strptime(ls.start_time, "%H:%M").time())
        end_dt = start_dt + timedelta(hours=ls.duration_hours)
        if end_dt.replace(tzinfo=now_.tzinfo) < now_:
            completed.append(ls)
    for ls in completed:
        ls.status = "已完成"
    db.commit()
    return len(completed)


# ---------------------------- lesson CRUD ----------------------------


ALLOWED_STATUS_TRANSITIONS = {
    "待上": {"待上", "已完成"},
    "已完成": {"已完成", "待上"},
    "请假": {"请假", "待上"},
    "已调课": {"已调课", "待上"},
}


def _invalid_transition(lesson: Lesson, target: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            "error": "invalid_status_transition",
            "message": f"{lesson.status}课程不能直接标记为{target}",
            "from_status": lesson.status,
            "to_status": target,
        },
    )


def _transition_lesson(db: Session, lesson: Lesson, target: str) -> Lesson:
    if target not in ALLOWED_STATUS_TRANSITIONS.get(lesson.status, set()):
        raise _invalid_transition(lesson, target)
    if target == lesson.status:
        return lesson
    if target == "待上":
        raise_if_conflict(
            db,
            on_date=lesson.date,
            start_time=lesson.start_time,
            duration_hours=lesson.duration_hours,
            exclude_lesson_id=lesson.id,
        )
        if lesson.status == "已调课" and lesson.rescheduled_to_id:
            new_lesson = db.get(Lesson, lesson.rescheduled_to_id)
            if new_lesson:
                if new_lesson.status == "待上":
                    # 恢复旧课时时同步取消替换生成的新课，避免新旧双排
                    new_lesson.status = "请假"
                    new_lesson.rescheduled_from_id = None
                else:
                    new_lesson.rescheduled_from_id = None
            lesson.rescheduled_to_id = None
    lesson.status = target
    return lesson


def _cancel_lesson(lesson: Lesson, note: str | None = None) -> Lesson:
    if lesson.status == "请假":
        return lesson
    if lesson.status != "待上":
        raise _invalid_transition(lesson, "请假")
    lesson.status = "请假"
    if note is not None:
        lesson.note = note
    return lesson


def _restore_lesson(db: Session, lesson: Lesson) -> Lesson:
    if lesson.status == "待上":
        return lesson
    return _transition_lesson(db, lesson, "待上")


def _delete_lesson(db: Session, lesson: Lesson) -> None:
    if lesson.template_id and lesson.date >= today():
        # 记录墓碑，防止夜间滚动任务/模板生成重建该课时
        db.add(
            TemplateLessonTombstone(
                template_id=lesson.template_id,
                date=lesson.date,
            )
        )
    db.delete(lesson)


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

    if new_status != ls.status:
        _transition_lesson(db, ls, new_status)
        data.pop("status", None)

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
    if old.status != "待上":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "invalid_status_transition",
                "message": f"{old.status}课程不能直接调课",
                "from_status": old.status,
                "to_status": "已调课",
            },
        )
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
    _cancel_lesson(ls, note)
    db.commit()
    db.refresh(ls)
    return ls


def restore_lesson(db: Session, lesson_id: int) -> Lesson:
    ls = get_lesson(db, lesson_id)
    _restore_lesson(db, ls)
    db.commit()
    db.refresh(ls)
    return ls


def delete_lesson(db: Session, lesson_id: int) -> None:
    ls = get_lesson(db, lesson_id)
    _delete_lesson(db, ls)
    db.commit()


def bulk_action(
    db: Session,
    *,
    lesson_ids: list[int],
    action: str,
    note: str | None = None,
) -> dict[str, int]:
    if action not in {"delete", "complete", "cancel", "restore"}:
        raise HTTPException(status_code=400, detail="不支持的批量操作")
    unique_ids = list(dict.fromkeys(lesson_ids))
    lessons = list(db.execute(select(Lesson).where(Lesson.id.in_(unique_ids))).scalars())
    by_id = {lesson.id: lesson for lesson in lessons}
    missing = [lesson_id for lesson_id in unique_ids if lesson_id not in by_id]
    if missing:
        raise HTTPException(
            status_code=404,
            detail={"error": "lesson_not_found", "lesson_id": missing[0]},
        )
    affected = 0
    try:
        for lesson_id in unique_ids:
            lesson = by_id[lesson_id]
            before = lesson.status
            try:
                if action == "delete":
                    _delete_lesson(db, lesson)
                elif action == "complete":
                    _transition_lesson(db, lesson, "已完成")
                elif action == "cancel":
                    _cancel_lesson(lesson, note)
                else:
                    _restore_lesson(db, lesson)
            except HTTPException as exc:
                detail = exc.detail if isinstance(exc.detail, dict) else {"message": exc.detail}
                raise HTTPException(
                    status_code=exc.status_code,
                    detail={**detail, "lesson_id": lesson_id},
                ) from exc
            if action == "delete" or lesson.status != before:
                affected += 1
        db.commit()
        return {"affected": affected}
    except Exception:
        db.rollback()
        raise

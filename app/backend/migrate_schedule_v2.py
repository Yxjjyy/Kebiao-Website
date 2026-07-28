"""迁移脚本 v2：2026-07-13 起调整课程安排，删除骆霖君课程。"""
import sys
from datetime import date, datetime

sys.path.insert(0, "/home/kebiao/app/backend")

from sqlalchemy import delete
from app.database import SessionLocal
from app.models import Lesson, ScheduleTemplate
from app.services.lesson_service import materialize_template

OLD_TEMPLATE_IDS = {18, 19, 20, 21, 22, 23, 24, 25, 26, 30, 31, 39, 42, 43}

# student_id -> [(day_of_week, start_time), ...]  0=Mon
NEW_PATTERNS = {
    3:  [(1, "09:00"), (3, "09:00"), (5, "09:00")],  # 娜娜: 二/四/六 9:00
    4:  [(0, "09:00"), (2, "09:00"), (4, "09:00")],  # 小雨: 一/三/五 9:00
    5:  [(0, "10:00"), (2, "10:00"), (4, "10:00")],  # vivi: 一/三/五 10:00
    7:  [(1, "10:00"), (3, "10:00"), (5, "10:00")],  # 婷婷: 二/四/六 10:00
    10: [(0, "14:00")],                                 # 哥哥数学: 一 14:00
}

EFFECTIVE_FROM = date(2026, 7, 13)


def main():
    db = SessionLocal()
    try:
        print("=== Step 1: 删除目标学生 7/13 之后的待上课时 ===")
        target_student_ids = set(NEW_PATTERNS.keys()) | {11}
        result = db.execute(
            delete(Lesson).where(
                Lesson.student_id.in_(target_student_ids),
                Lesson.date >= EFFECTIVE_FROM,
                Lesson.status == "待上",
            )
        )
        db.commit()
        print(f"  删除课时: {result.rowcount} 条")

        print("=== Step 2: 删除旧 schedule_templates ===")
        result = db.execute(
            delete(ScheduleTemplate).where(ScheduleTemplate.id.in_(OLD_TEMPLATE_IDS))
        )
        db.commit()
        print(f"  删除模板: {result.rowcount} 条")

        print("=== Step 3: 创建新 schedule_templates ===")
        now = datetime.utcnow()
        new_templates = []
        for student_id, slots in NEW_PATTERNS.items():
            for day_of_week, start_time in slots:
                t = ScheduleTemplate(
                    student_id=student_id,
                    day_of_week=day_of_week,
                    start_time=start_time,
                    duration_hours=1.0,
                    effective_from=EFFECTIVE_FROM,
                    effective_to=None,
                    repeat_interval=1,
                    created_at=now,
                    updated_at=now,
                )
                db.add(t)
                db.flush()
                new_templates.append((t.id, student_id, day_of_week, start_time))
        db.commit()
        print(f"  创建模板: {len(new_templates)} 条")

        print("=== Step 4: 按新模板生成 lessons ===")
        total_created = 0
        for tid, sid, dow, stime in new_templates:
            template = db.get(ScheduleTemplate, tid)
            if template is None:
                print(f"  WARN: 模板 {tid} 未找到")
                continue
            n = materialize_template(db, template, from_date=EFFECTIVE_FROM)
            if n > 0:
                print(f"  模板 {tid}: student={sid}, day={dow}, time={stime} -> 生成 {n} 节课")
            total_created += n
        print(f"  共生成: {total_created} 节课")

        print("\n=== 迁移完成 ===")

    finally:
        db.close()


if __name__ == "__main__":
    main()

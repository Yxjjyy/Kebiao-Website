"""迁移脚本：将6月11日后课程改为5/25-5/31参考周模式，删除小鱼课程，保留灿灿。"""

import sys
from datetime import date, datetime

sys.path.insert(0, "/home/kebiao/app/backend")

from sqlalchemy import delete
from app.database import SessionLocal
from app.models import Lesson, ScheduleTemplate
from app.services.lesson_service import materialize_template


REFERENCE_WEEK_PATTERN = {
    # student_id -> [(day_of_week, start_time), ...]
    # 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
    3:  [(0, "18:05"), (2, "18:05"), (5, "18:05")],  # 娜娜
    4:  [(0, "19:10"), (2, "19:10"), (5, "14:00")],  # 哥哥
    5:  [(1, "19:10"), (3, "19:10"), (5, "15:05")],  # 妹妹
    6:  [(0, "20:15"), (2, "20:15"), (4, "18:15")],  # 石头
    7:  [(1, "18:05"), (3, "18:05")],                # 姐姐
    8:  [(0, "21:20"), (1, "21:15"), (2, "21:20"),   # 八月
          (3, "21:15"), (4, "21:05"), (5, "21:10"),
          (6, "21:00")],
}

EFFECTIVE_FROM = date(2026, 6, 11)

# 不变的学生: 灿灿(1), 小鱼(2 archived), 哥哥数学(10), 骆霖君(11), 向俞松(12 archived/13 active)
UNCHANGED_STUDENT_IDS = {1, 2, 10, 11, 12, 13}
# 要删除小鱼: student_id=9 (active)
XIAOYU_ACTIVE_ID = 9
# 要清空旧课+重建模板的学生
TARGET_STUDENT_IDS = {3, 4, 5, 6, 7, 8}

# 要删除的旧模板ID
OLD_TEMPLATE_IDS = {1, 3, 9, 11, 12, 13, 14, 15, 16}


def main():
    db = SessionLocal()
    try:
        print("=== Step 1: 删除小鱼的 schedule_templates ===")
        result = db.execute(
            delete(ScheduleTemplate).where(ScheduleTemplate.student_id == XIAOYU_ACTIVE_ID)
        )
        print(f"  删除模板: {result.rowcount} 条")

        print("=== Step 2: 删除小鱼 (student_id=9) 6/11之后的 lessons ===")
        result = db.execute(
            delete(Lesson).where(
                Lesson.student_id == XIAOYU_ACTIVE_ID,
                Lesson.date >= EFFECTIVE_FROM,
            )
        )
        print(f"  删除课程: {result.rowcount} 条")

        print("=== Step 3: 清空目标学生 (娜娜/哥哥/妹妹/石头/姐姐/八月) 6/11之后的 lessons ===")
        result = db.execute(
            delete(Lesson).where(
                Lesson.student_id.in_(TARGET_STUDENT_IDS),
                Lesson.date >= EFFECTIVE_FROM,
            )
        )
        print(f"  删除课程: {result.rowcount} 条")

        print("=== Step 4: 删除旧的 schedule_templates ===")
        result = db.execute(
            delete(ScheduleTemplate).where(ScheduleTemplate.id.in_(OLD_TEMPLATE_IDS))
        )
        print(f"  删除模板: {result.rowcount} 条")

        db.commit()
        print("  前4步提交成功")

        print("=== Step 5: 创建新 schedule_templates ===")
        now = datetime.utcnow()
        new_template_ids = []
        for student_id, slots in REFERENCE_WEEK_PATTERN.items():
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
                new_template_ids.append((t.id, student_id, day_of_week, start_time))
        db.commit()
        print(f"  创建模板: {len(new_template_ids)} 条")

        print("=== Step 6: 按新模板生成 lessons ===")
        total_created = 0
        for tid, sid, dow, stime in new_template_ids:
            template = db.get(ScheduleTemplate, tid)
            if template is None:
                print(f"  WARN: 模板 {tid} 未找到")
                continue
            n = materialize_template(db, template, from_date=EFFECTIVE_FROM)
            if n > 0:
                print(f"  模板 {tid}: student={sid}, day={dow}, time={stime} → 生成 {n} 节课")
            total_created += n
        print(f"  共生成: {total_created} 节课")

        print("\n=== 迁移完成 ===")

    finally:
        db.close()


if __name__ == "__main__":
    main()

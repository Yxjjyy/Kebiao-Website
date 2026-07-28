"""Import lessons from ../class-schedule.html into the local SQLite database.

This importer mirrors the JavaScript constants in class-schedule.html. The
source file does not contain tuition rates, so students are created with a
placeholder hourly_rate=1.0 for later editing in the UI.
"""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Lesson, Student

COLORS = {
    "男雅思": "#1565C0",
    "小鱼": "#00897B",
    "娜娜": "#E65100",
    "哥哥": "#EF6C00",
    "妹妹": "#C62828",
    "石头": "#4E342E",
    "姐姐": "#AD1457",
    "八月": "#283593",
}

WEEKS = [
    {
        "label": "第1周",
        "start": date(2026, 5, 11),
        "end": date(2026, 5, 17),
        "type": "单周",
        "ielts": "11:00-12:00",
        "exclude_mon_ielts": True,
    },
    {
        "label": "第2周",
        "start": date(2026, 5, 18),
        "end": date(2026, 5, 24),
        "type": "双周",
        "ielts": "13:00-14:00",
    },
    {
        "label": "第3周",
        "start": date(2026, 5, 25),
        "end": date(2026, 5, 31),
        "type": "单周",
        "ielts": "11:00-12:00",
    },
    {
        "label": "第4周",
        "start": date(2026, 6, 1),
        "end": date(2026, 6, 7),
        "type": "双周",
        "ielts": "13:00-14:00",
    },
    {
        "label": "第5周",
        "start": date(2026, 6, 8),
        "end": date(2026, 6, 10),
        "type": "单周",
        "ielts": "11:00-12:00",
    },
]

BASE = {
    0: [
        ("17:00-18:00", "小鱼", ""),
        ("18:05-19:05", "娜娜", "①"),
        ("19:10-20:10", "哥哥", ""),
        ("20:15-21:15", "石头", ""),
        ("21:20-22:20", "八月", ""),
    ],
    1: [
        ("18:05-19:05", "姐姐", "①"),
        ("19:10-20:10", "妹妹", ""),
        ("21:15-22:15", "八月", ""),
    ],
    2: [
        ("18:05-19:05", "娜娜", "②"),
        ("19:10-20:10", "哥哥", ""),
        ("20:15-21:15", "石头", ""),
        ("21:20-22:20", "八月", ""),
    ],
    3: [
        ("17:00-18:00", "小鱼", ""),
        ("18:05-19:05", "姐姐", "②"),
        ("19:10-20:10", "妹妹", ""),
        ("21:15-22:15", "八月", ""),
    ],
    4: [
        ("18:15-19:15", "石头", ""),
        ("19:30-21:00", "空置", "不排课"),
        ("21:05-22:05", "八月", ""),
    ],
    5: [
        ("14:00-15:00", "哥哥", ""),
        ("15:05-16:05", "妹妹", ""),
        ("17:00-18:00", "小鱼", ""),
        ("18:05-19:05", "娜娜", "③"),
        ("21:10-22:10", "八月", ""),
    ],
    6: [
        ("21:00-22:00", "八月", "备用"),
    ],
}


def duration_hours(range_text: str) -> float:
    start, end = range_text.split("-")
    sh, sm = [int(part) for part in start.split(":")]
    eh, em = [int(part) for part in end.split(":")]
    return ((eh * 60 + em) - (sh * 60 + sm)) / 60


def iter_dates(start: date, end: date):
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)


def slots_for_day(week: dict, weekday: int):
    slots = list(BASE.get(weekday, []))
    if weekday in {0, 2, 4, 6} and not (
        weekday == 0 and week.get("exclude_mon_ielts")
    ):
        slots.insert(0, (week["ielts"], "男雅思", week["type"]))
    return [slot for slot in slots if slot[1] != "空置"]


def main() -> None:
    db = SessionLocal()
    try:
        students: dict[str, Student] = {}
        for name, color in COLORS.items():
            student = db.execute(select(Student).where(Student.name == name)).scalar_one_or_none()
            if student is None:
                student = Student(
                    name=name,
                    color=color,
                    hourly_rate=1.0,
                    note="从 class-schedule.html 导入",
                )
                db.add(student)
                db.flush()
            else:
                student.color = color
            students[name] = student

        created = 0
        skipped = 0
        for week in WEEKS:
            for d in iter_dates(week["start"], week["end"]):
                for range_text, name, note_suffix in slots_for_day(week, d.weekday()):
                    start_time = range_text.split("-")[0]
                    exists = db.execute(
                        select(Lesson).where(
                            Lesson.student_id == students[name].id,
                            Lesson.date == d,
                            Lesson.start_time == start_time,
                        )
                    ).scalar_one_or_none()
                    if exists:
                        skipped += 1
                        continue
                    note_parts = [week["label"], week["type"]]
                    if note_suffix:
                        note_parts.append(note_suffix)
                    lesson = Lesson(
                        student_id=students[name].id,
                        template_id=None,
                        date=d,
                        start_time=start_time,
                        duration_hours=duration_hours(range_text),
                        status="待上",
                        price=students[name].hourly_rate * duration_hours(range_text),
                        note=" / ".join(note_parts),
                    )
                    db.add(lesson)
                    created += 1
        db.commit()
        print(f"import complete: students={len(students)}, lessons_created={created}, skipped={skipped}")
    finally:
        db.close()


if __name__ == "__main__":
    main()

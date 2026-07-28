from sqlalchemy import func, select

from app.database import SessionLocal
from app.models import Lesson, Student

db = SessionLocal()
try:
    print("students", db.execute(select(func.count(Student.id))).scalar_one())
    print("lessons", db.execute(select(func.count(Lesson.id))).scalar_one())
    print("range", db.execute(select(func.min(Lesson.date), func.max(Lesson.date))).one())
    for row in db.execute(select(Student.name, Student.color).order_by(Student.name)).all():
        print("student", row.name, row.color)
    for lesson in db.execute(
        select(Lesson).order_by(Lesson.date, Lesson.start_time).limit(8)
    ).scalars():
        print(
            "lesson",
            lesson.date,
            lesson.start_time,
            lesson.student.name,
            lesson.duration_hours,
            lesson.note,
        )
finally:
    db.close()

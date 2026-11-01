from datetime import date, timedelta

import pytest
from fastapi import HTTPException

from app.models import Lesson, Student
from app.services import lesson_service
from app.timeutil import today


def future_weekday(weekday: int = 0) -> date:
    base = today() + timedelta(days=1)
    return base + timedelta(days=(weekday - base.weekday()) % 7)


def create_student(client, name: str = "冲突测试") -> dict:
    response = client.post(
        "/api/v1/students",
        json={"name": name, "color": "#8b5cf6", "hourly_rate": 200},
    )
    assert response.status_code == 200
    return response.json()


def create_lesson(client, student_id: int, on_date: date, start: str = "10:00") -> dict:
    response = client.post(
        "/api/v1/lessons",
        json={
            "student_id": student_id,
            "date": on_date.isoformat(),
            "start_time": start,
            "duration_hours": 1,
        },
    )
    assert response.status_code == 200
    return response.json()


def list_lessons(client, on_date: date) -> list[dict]:
    response = client.get(
        "/api/v1/lessons",
        params={"from": on_date.isoformat(), "to": on_date.isoformat()},
    )
    assert response.status_code == 200
    return response.json()


def test_create_template_conflict_returns_409_without_persisting(client):
    student = create_student(client)
    target = future_weekday()
    existing = create_lesson(client, student["id"], target)

    response = client.post(
        "/api/v1/templates",
        json={
            "student_id": student["id"],
            "day_of_week": target.weekday(),
            "start_time": "10:00",
            "duration_hours": 1,
            "effective_from": target.isoformat(),
            "effective_to": target.isoformat(),
            "repeat_interval": 1,
        },
    )

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["error"] == "time_conflict"
    assert detail["conflicts"][0]["date"] == target.isoformat()
    assert client.get("/api/v1/templates").json() == []
    assert [row["id"] for row in list_lessons(client, target)] == [existing["id"]]


def test_update_template_conflict_rolls_back_deleted_lessons(client):
    student = create_student(client)
    target = future_weekday()
    created = client.post(
        "/api/v1/templates",
        json={
            "student_id": student["id"],
            "day_of_week": target.weekday(),
            "start_time": "09:00",
            "duration_hours": 1,
            "effective_from": target.isoformat(),
            "effective_to": target.isoformat(),
            "repeat_interval": 1,
        },
    )
    assert created.status_code == 200
    template = created.json()["template"]
    template_lesson = list_lessons(client, target)[0]
    manual = create_lesson(client, student["id"], target, start="11:00")

    response = client.patch(
        f"/api/v1/templates/{template['id']}",
        json={
            "start_time": "11:00",
            "apply_mode": "from_date",
            "apply_from_date": target.isoformat(),
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"]["error"] == "time_conflict"
    templates = client.get("/api/v1/templates").json()
    assert len(templates) == 1
    assert templates[0]["start_time"] == "09:00"
    rows = list_lessons(client, target)
    assert {(row["start_time"], row["id"]) for row in rows} == {
        ("09:00", template_lesson["id"]),
        ("11:00", manual["id"]),
    }


def test_update_template_without_conflict_rebuilds_future_lessons(client):
    student = create_student(client)
    target = future_weekday()
    created = client.post(
        "/api/v1/templates",
        json={
            "student_id": student["id"],
            "day_of_week": target.weekday(),
            "start_time": "09:00",
            "duration_hours": 1,
            "effective_from": target.isoformat(),
            "effective_to": target.isoformat(),
            "repeat_interval": 1,
        },
    )
    template = created.json()["template"]

    response = client.patch(
        f"/api/v1/templates/{template['id']}",
        json={
            "start_time": "10:00",
            "apply_mode": "from_date",
            "apply_from_date": target.isoformat(),
        },
    )

    assert response.status_code == 200
    assert response.json()["regenerated_lessons"] == 1
    rows = list_lessons(client, target)
    assert [row["start_time"] for row in rows] == ["10:00"]


def test_template_effective_range_is_validated(client):
    student = create_student(client)
    target = future_weekday()
    invalid_to = (target - timedelta(days=1)).isoformat()

    response = client.post(
        "/api/v1/templates",
        json={
            "student_id": student["id"],
            "day_of_week": target.weekday(),
            "start_time": "12:00",
            "duration_hours": 1,
            "effective_from": target.isoformat(),
            "effective_to": invalid_to,
            "repeat_interval": 1,
        },
    )
    assert response.status_code == 422
    assert client.get("/api/v1/templates").json() == []

    created = client.post(
        "/api/v1/templates",
        json={
            "student_id": student["id"],
            "day_of_week": target.weekday(),
            "start_time": "12:00",
            "duration_hours": 1,
            "effective_from": target.isoformat(),
            "effective_to": target.isoformat(),
            "repeat_interval": 1,
        },
    )
    template = created.json()["template"]

    response = client.patch(
        f"/api/v1/templates/{template['id']}",
        json={"effective_to": invalid_to, "apply_mode": "template_only"},
    )
    assert response.status_code == 422
    assert client.get("/api/v1/templates").json()[0]["effective_to"] == target.isoformat()


def test_patch_lesson_time_conflict_returns_409(client):
    student = create_student(client)
    target = future_weekday()
    first = create_lesson(client, student["id"], target, start="09:00")
    second = create_lesson(client, student["id"], target, start="11:00")

    response = client.patch(
        f"/api/v1/lessons/{second['id']}",
        json={"start_time": "09:30"},
    )

    assert response.status_code == 409
    assert response.json()["detail"]["error"] == "time_conflict"
    rows = {row["id"]: row["start_time"] for row in list_lessons(client, target)}
    assert rows == {first["id"]: "09:00", second["id"]: "11:00"}


def test_patch_lesson_null_status_is_a_noop(client):
    student = create_student(client)
    target = future_weekday()
    lesson = create_lesson(client, student["id"], target)

    response = client.patch(f"/api/v1/lessons/{lesson['id']}", json={"status": None})

    assert response.status_code == 200
    assert response.json()["status"] == "待上"


def test_today_summary_excludes_soft_deleted_lessons(client):
    student = create_student(client)
    lesson = create_lesson(client, student["id"], today())

    assert client.delete(f"/api/v1/lessons/{lesson['id']}").status_code == 204

    response = client.get("/api/v1/stats/today")
    assert response.status_code == 200
    assert lesson["id"] not in [row["id"] for row in response.json()["lessons"]]


def test_restoring_deleted_future_completed_lesson_checks_conflicts(db_session):
    student = Student(name="恢复冲突", color="#8b5cf6", hourly_rate=200)
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    target = future_weekday()

    deleted = Lesson(
        student_id=student.id,
        date=target,
        start_time="10:00",
        duration_hours=1,
        status="已完成",
        price=200,
    )
    blocker = Lesson(
        student_id=student.id,
        date=target,
        start_time="10:30",
        duration_hours=1,
        status="待上",
        price=200,
    )
    db_session.add_all([deleted, blocker])
    db_session.commit()
    db_session.refresh(deleted)
    db_session.refresh(blocker)

    lesson_service.delete_lesson(db_session, deleted.id)
    with pytest.raises(HTTPException) as raised:
        lesson_service.restore_lesson(db_session, deleted.id)

    assert raised.value.status_code == 409
    assert raised.value.detail["error"] == "time_conflict"
    db_session.expire_all()
    assert db_session.get(Lesson, deleted.id).status == "已删除"

import sqlite3

from app.config import Settings, get_settings


def create_student(client, name="林晓"):
    response = client.post(
        "/api/v1/students",
        headers={"X-Request-ID": "req-student"},
        json={"name": name, "color": "#8b5cf6", "hourly_rate": 200},
    )
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "req-student"
    return response.json()


def create_lesson(client, student_id, date="2026-08-13", start="10:00"):
    response = client.post(
        "/api/v1/lessons",
        json={"student_id": student_id, "date": date, "start_time": start, "duration_hours": 1},
    )
    assert response.status_code == 200
    return response.json()


def test_core_read_write_conflict_status_and_statistics(client):
    student = create_student(client)
    first = create_lesson(client, student["id"])
    second = create_lesson(client, student["id"], date="2026-08-14")

    conflict = client.post(
        "/api/v1/lessons",
        json={"student_id": student["id"], "date": "2026-08-13", "start_time": "10:30", "duration_hours": 1},
    )
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["error"] == "time_conflict"
    assert conflict.json()["detail"]["conflicts"][0]["student_name"] == "林晓"

    completed = client.patch(f"/api/v1/lessons/{first['id']}", json={"status": "已完成"})
    assert completed.status_code == 200
    invalid_cancel = client.post(f"/api/v1/lessons/{first['id']}/cancel")
    assert invalid_cancel.status_code == 409
    assert invalid_cancel.json()["detail"]["error"] == "invalid_status_transition"

    leave = client.post(f"/api/v1/lessons/{second['id']}/cancel")
    assert leave.status_code == 200
    restored = client.post(f"/api/v1/lessons/{second['id']}/restore")
    assert restored.status_code == 200
    assert restored.json()["status"] == "待上"

    client.post(f"/api/v1/lessons/{second['id']}/cancel")
    bulk = client.post(
        "/api/v1/lessons/bulk",
        json={"ids": [first["id"], second["id"]], "action": "complete"},
    )
    assert bulk.status_code == 409
    assert bulk.json()["detail"]["lesson_id"] == second["id"]
    rows = client.get("/api/v1/lessons", params={"from": "2026-08-13", "to": "2026-08-14"}).json()
    assert {row["id"]: row["status"] for row in rows} == {first["id"]: "已完成", second["id"]: "请假"}

    stats = client.get(
        "/api/v1/stats/range",
        params={"from": "2026-08-13", "to": "2026-08-14", "granularity": "day"},
    )
    assert stats.status_code == 200
    assert stats.json() | {
        "total_income": 200.0, "total_hours": 1.0, "completed_lessons": 1,
        "leave_count": 1, "reschedule_count": 0,
    } == stats.json()


def test_invalid_restore_keeps_route_database(client, test_app, tmp_path):
    target = tmp_path / "restore-target.db"
    with sqlite3.connect(target) as connection:
        connection.execute("CREATE TABLE sentinel (value TEXT)")
        connection.execute("INSERT INTO sentinel VALUES ('keep')")
    test_app.dependency_overrides[get_settings] = lambda: Settings(DB_PATH=str(target), MAX_RESTORE_BYTES=1024)

    response = client.post(
        "/api/v1/restore",
        headers={"X-Confirm-Restore": "yes"},
        files={"file": ("bad.db", b"not sqlite")},
    )

    assert response.status_code == 422
    with sqlite3.connect(target) as connection:
        assert connection.execute("SELECT value FROM sentinel").fetchone() == ("keep",)

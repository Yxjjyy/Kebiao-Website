def test_invalid_route_transition_returns_structured_conflict(client):
    student = client.post(
        "/api/v1/students",
        json={"name": "林晓", "color": "#8b5cf6", "hourly_rate": 200},
    ).json()
    lesson = client.post(
        "/api/v1/lessons",
        json={
            "student_id": student["id"], "date": "2026-08-13", "start_time": "10:00",
            "duration_hours": 1,
        },
    ).json()
    client.patch(f"/api/v1/lessons/{lesson['id']}", json={"status": "已完成"})

    response = client.post(f"/api/v1/lessons/{lesson['id']}/cancel")

    assert response.status_code == 409
    assert response.json()["detail"] == {
        "error": "invalid_status_transition",
        "message": "已完成课程不能直接标记为请假",
        "from_status": "已完成",
        "to_status": "请假",
    }


def _soft_delete_helper(client):
    student = client.post(
        "/api/v1/students",
        json={"name": "软删", "color": "#8b5cf6", "hourly_rate": 100},
    ).json()
    lesson = client.post(
        "/api/v1/lessons",
        json={
            "student_id": student["id"], "date": "2026-08-20", "start_time": "10:00",
            "duration_hours": 1,
        },
    ).json()
    return student, lesson


def test_delete_lesson_is_soft_and_excluded_from_list(client):
    _, lesson = _soft_delete_helper(client)

    response = client.delete(f"/api/v1/lessons/{lesson['id']}")
    assert response.status_code == 204

    listed = client.get(
        "/api/v1/lessons",
        params={"from": "2026-08-20", "to": "2026-08-20"},
    ).json()
    assert lesson["id"] not in [item["id"] for item in listed]

    client.post(f"/api/v1/lessons/{lesson['id']}/restore")
    restored = client.get(
        "/api/v1/lessons",
        params={"from": "2026-08-20", "to": "2026-08-20"},
    ).json()
    assert lesson["id"] in [item["id"] for item in restored]


def test_delete_completed_lesson_restores_to_completed(client):
    student, lesson = _soft_delete_helper(client)
    client.patch(f"/api/v1/lessons/{lesson['id']}", json={"status": "已完成"})

    client.delete(f"/api/v1/lessons/{lesson['id']}")
    client.post(f"/api/v1/lessons/{lesson['id']}/restore")

    listed = client.get(
        "/api/v1/lessons",
        params={"from": "2026-08-20", "to": "2026-08-20"},
    ).json()
    item = next(item for item in listed if item["id"] == lesson["id"])
    assert item["status"] == "已完成"


def test_double_delete_is_idempotent(client):
    _, lesson = _soft_delete_helper(client)
    assert client.delete(f"/api/v1/lessons/{lesson['id']}").status_code == 204
    assert client.delete(f"/api/v1/lessons/{lesson['id']}").status_code == 204

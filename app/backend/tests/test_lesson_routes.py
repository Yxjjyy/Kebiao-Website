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

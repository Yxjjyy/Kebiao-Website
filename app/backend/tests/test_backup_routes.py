import sqlite3

from app.config import Settings, get_settings


def test_restore_route_requires_confirmation(client):
    response = client.post("/api/v1/restore", files={"file": ("backup.db", b"data")})
    assert response.status_code == 400


def test_restore_route_maps_invalid_sqlite_to_422(client, test_app, tmp_path):
    target = tmp_path / "route.db"
    connection = sqlite3.connect(target)
    connection.execute("CREATE TABLE keep_me (id INTEGER)")
    connection.commit()
    connection.close()
    test_app.dependency_overrides[get_settings] = lambda: Settings(DB_PATH=str(target), MAX_RESTORE_BYTES=1024)

    response = client.post(
        "/api/v1/restore",
        headers={"X-Confirm-Restore": "yes", "X-Request-ID": "req-restore"},
        files={"file": ("backup.db", b"not sqlite")},
    )

    assert response.status_code == 422
    assert response.headers["X-Request-ID"] == "req-restore"
    with sqlite3.connect(target) as check:
        assert check.execute("SELECT name FROM sqlite_master WHERE name='keep_me'").fetchone()

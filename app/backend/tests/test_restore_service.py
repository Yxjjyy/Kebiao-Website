import asyncio
import hashlib
import sqlite3
from pathlib import Path

import pytest
from fastapi import UploadFile

from app.services import restore_service


CORE_TABLES = {
    "students", "schedule_templates", "lessons", "settings", "user_profile", "alembic_version",
}


def sqlite_file(path: Path, marker: str, tables=CORE_TABLES) -> Path:
    connection = sqlite3.connect(path)
    for table in tables:
        if table == "alembic_version":
            connection.execute("CREATE TABLE alembic_version (version_num TEXT PRIMARY KEY)")
            connection.execute("INSERT INTO alembic_version VALUES ('0001')")
        else:
            connection.execute(f'CREATE TABLE "{table}" (id INTEGER PRIMARY KEY, marker TEXT)')
    connection.execute("CREATE TABLE restore_marker (value TEXT)")
    connection.execute("INSERT INTO restore_marker VALUES (?)", (marker,))
    connection.commit()
    connection.close()
    return path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def upload(path: Path) -> UploadFile:
    return UploadFile(filename=path.name, file=path.open("rb"))


@pytest.mark.parametrize("kind", ["text", "corrupt", "missing_tables", "too_large"])
def test_invalid_restore_preserves_database_and_cleans_temp(tmp_path, kind):
    current = sqlite_file(tmp_path / "app.db", "old")
    before = digest(current)
    candidate = tmp_path / "candidate.db"
    max_bytes = 1024 * 1024
    if kind == "text":
        candidate.write_text("not sqlite", encoding="utf-8")
    elif kind == "corrupt":
        candidate.write_bytes(b"SQLite format 3\x00" + b"broken" * 100)
    elif kind == "missing_tables":
        sqlite_file(candidate, "new", {"students", "alembic_version"})
    else:
        candidate.write_bytes(b"x" * 128)
        max_bytes = 64

    with pytest.raises(restore_service.RestoreValidationError):
        asyncio.run(restore_service.restore_database(upload(candidate), current, max_bytes=max_bytes))

    assert digest(current) == before
    assert not list(tmp_path.glob(".restore-*.db"))


def test_backup_failure_preserves_database(tmp_path, monkeypatch):
    current = sqlite_file(tmp_path / "app.db", "old")
    candidate = sqlite_file(tmp_path / "candidate.db", "new")
    before = digest(current)

    monkeypatch.setattr(restore_service, "create_consistent_backup", lambda *_: (_ for _ in ()).throw(OSError("backup failed")))
    with pytest.raises(restore_service.RestoreOperationError):
        asyncio.run(restore_service.restore_database(upload(candidate), current, max_bytes=10_000_000))
    assert digest(current) == before
    assert not list(tmp_path.glob(".restore-*.db"))


def test_replace_failure_preserves_database(tmp_path, monkeypatch):
    current = sqlite_file(tmp_path / "app.db", "old")
    candidate = sqlite_file(tmp_path / "candidate.db", "new")
    before = digest(current)
    real_replace = restore_service.os.replace

    def fail_candidate_replace(source, target):
        if Path(source).name.startswith(".restore-") and "rollback" not in Path(source).name:
            raise OSError("replace failed")
        return real_replace(source, target)

    monkeypatch.setattr(restore_service.os, "replace", fail_candidate_replace)
    with pytest.raises(restore_service.RestoreOperationError):
        asyncio.run(restore_service.restore_database(upload(candidate), current, max_bytes=10_000_000))

    assert digest(current) == before
    assert not list(tmp_path.glob(".restore-*.db"))


def test_post_replace_validation_failure_restores_old_database(tmp_path, monkeypatch):
    current = sqlite_file(tmp_path / "app.db", "old")
    candidate = sqlite_file(tmp_path / "candidate.db", "new")
    before = digest(current)
    real_validate = restore_service.validate_sqlite
    calls = 0

    def fail_second_validation(path):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise restore_service.RestoreValidationError("post replace failure")
        return real_validate(path)

    monkeypatch.setattr(restore_service, "validate_sqlite", fail_second_validation)
    with pytest.raises(restore_service.RestoreOperationError):
        asyncio.run(restore_service.restore_database(upload(candidate), current, max_bytes=10_000_000))

    assert digest(current) == before
    with sqlite3.connect(current) as connection:
        assert connection.execute("SELECT value FROM restore_marker").fetchone() == ("old",)


def test_successful_restore_keeps_timestamped_old_copy(tmp_path):
    current = sqlite_file(tmp_path / "app.db", "old")
    candidate = sqlite_file(tmp_path / "candidate.db", "new")

    result = asyncio.run(restore_service.restore_database(upload(candidate), current, max_bytes=10_000_000))

    with sqlite3.connect(current) as connection:
        assert connection.execute("SELECT value FROM restore_marker").fetchone() == ("new",)
    old_copy = Path(result.old_saved_at)
    assert old_copy.exists()
    assert old_copy.name.startswith("app-before-restore-")
    assert old_copy.name.endswith(".db")
    assert len(old_copy.stem.rsplit("-", 2)[-2] + old_copy.stem.rsplit("-", 2)[-1]) == 14
    assert not list(tmp_path.glob(".restore-*.db"))

import os
import sqlite3
import tempfile
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from fastapi import UploadFile

CORE_TABLES = {
    "students",
    "schedule_templates",
    "lessons",
    "settings",
    "user_profiles",
    "alembic_version",
}


class RestoreValidationError(ValueError):
    pass


class RestoreOperationError(RuntimeError):
    pass


@dataclass(frozen=True)
class RestoreResult:
    restored_to: str
    old_saved_at: str


def validate_sqlite(path: Path) -> None:
    try:
        with path.open("rb") as source:
            if source.read(16) != b"SQLite format 3\x00":
                raise RestoreValidationError("上传文件不是 SQLite 数据库")
        with closing(sqlite3.connect(f"file:{path}?mode=ro", uri=True)) as connection:
            integrity = connection.execute("PRAGMA integrity_check").fetchone()
            if not integrity or integrity[0] != "ok":
                raise RestoreValidationError("SQLite 完整性检查失败")
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            missing = sorted(CORE_TABLES - tables)
            if missing:
                raise RestoreValidationError(f"数据库缺少核心表：{', '.join(missing)}")
    except RestoreValidationError:
        raise
    except sqlite3.DatabaseError as exc:
        raise RestoreValidationError("SQLite 文件已损坏或无法读取") from exc
    except OSError as exc:
        raise RestoreValidationError("上传文件无法读取") from exc


def create_consistent_backup(source: Path, target: Path) -> None:
    source_connection = sqlite3.connect(source)
    target_connection = sqlite3.connect(target)
    try:
        source_connection.backup(target_connection)
    finally:
        target_connection.close()
        source_connection.close()


async def _save_upload(upload: UploadFile, target: Path, max_bytes: int) -> None:
    total = 0
    with target.open("wb") as destination:
        while chunk := await upload.read(1024 * 1024):
            total += len(chunk)
            if total > max_bytes:
                raise RestoreValidationError("上传数据库超过允许大小")
            destination.write(chunk)
    if total == 0:
        raise RestoreValidationError("上传数据库为空")


async def restore_database(
    upload: UploadFile,
    db_path: Path,
    *,
    max_bytes: int,
    dispose_connections=None,
) -> RestoreResult:
    db_path = db_path.resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".restore-", suffix=".db", dir=db_path.parent,
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = db_path.with_name(f"{db_path.stem}-before-restore-{timestamp}.db")
    rollback = db_path.with_name(f".restore-rollback-{db_path.name}")
    replaced = False
    original_moved = False
    try:
        await _save_upload(upload, temporary, max_bytes)
        validate_sqlite(temporary)
        if db_path.exists():
            try:
                create_consistent_backup(db_path, backup)
            except (OSError, sqlite3.DatabaseError) as exc:
                backup.unlink(missing_ok=True)
                raise RestoreOperationError("创建当前数据库备份失败") from exc
        if dispose_connections is not None:
            dispose_connections()
        try:
            if db_path.exists():
                os.replace(db_path, rollback)
                original_moved = True
            os.replace(temporary, db_path)
            replaced = True
            validate_sqlite(db_path)
        except Exception as exc:
            if replaced:
                db_path.unlink(missing_ok=True)
            if original_moved and rollback.exists():
                os.replace(rollback, db_path)
            if isinstance(exc, RestoreValidationError):
                raise RestoreOperationError("替换后的数据库验证失败，已恢复原数据库") from exc
            raise RestoreOperationError("数据库原子替换失败") from exc
        rollback.unlink(missing_ok=True)
        return RestoreResult(restored_to=str(db_path), old_saved_at=str(backup))
    finally:
        temporary.unlink(missing_ok=True)
        if rollback.exists() and not db_path.exists():
            os.replace(rollback, db_path)

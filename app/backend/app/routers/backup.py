"""备份/恢复路由。"""

import asyncio
import sqlite3
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from app.config import Settings, get_settings
from app.database import engine
from app.services.restore_service import (
    RestoreOperationError,
    RestoreValidationError,
    restore_database,
)

router = APIRouter(tags=["backup"])

# restore 在进程内串行化，避免并发替换窗口期冲突
_restore_lock = asyncio.Lock()


@router.get("/backup")
def download_backup(settings: Settings = Depends(get_settings)):
    db_path = Path(settings.DB_PATH).resolve()
    if not db_path.exists():
        raise HTTPException(status_code=404, detail="数据库不存在")

    # 用 sqlite3 .backup 复制出一致的快照
    tmp_path = Path(tempfile.mkstemp(suffix=".db")[1])
    src = sqlite3.connect(str(db_path))
    dst = sqlite3.connect(str(tmp_path))
    with dst:
        src.backup(dst)
    src.close()
    dst.close()
    return FileResponse(
        path=tmp_path,
        filename="kebiao-backup.db",
        media_type="application/octet-stream",
        background=BackgroundTask(tmp_path.unlink, missing_ok=True),
    )


@router.post("/restore")
async def upload_restore(
    file: UploadFile = File(...),
    x_confirm_restore: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
):
    if x_confirm_restore != "yes":
        raise HTTPException(
            status_code=400,
            detail="须带 X-Confirm-Restore: yes 头部以确认覆盖操作",
        )
    db_path = Path(settings.DB_PATH).resolve()
    async with _restore_lock:
        try:
            result = await restore_database(
                file,
                db_path,
                max_bytes=settings.MAX_RESTORE_BYTES,
                dispose_connections=engine.dispose,
            )
        except RestoreValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except RestoreOperationError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"ok": True, **result.__dict__}

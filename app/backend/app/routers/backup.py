"""备份/恢复路由。"""

import shutil
import sqlite3
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.config import Settings, get_settings

router = APIRouter(tags=["backup"])


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
    db_path.parent.mkdir(parents=True, exist_ok=True)
    backup_old = db_path.with_suffix(".db.bak")
    if db_path.exists():
        shutil.copy2(db_path, backup_old)
    with open(db_path, "wb") as f:
        content = await file.read()
        f.write(content)
    return {"ok": True, "restored_to": str(db_path), "old_saved_at": str(backup_old)}

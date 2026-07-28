from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import Settings, UserProfile
from app.schemas.settings import (
    ProfileOut,
    ProfileUpdate,
    SettingsOut,
    SettingsUpdate,
)

router = APIRouter(tags=["settings"])


@router.get("/settings", response_model=SettingsOut)
def get_settings(db: Session = Depends(get_db)):
    s = db.get(Settings, 1)
    if not s:
        raise HTTPException(status_code=500, detail="设置未初始化")
    return SettingsOut.model_validate(s)


@router.patch("/settings", response_model=SettingsOut)
def update_settings(payload: SettingsUpdate, db: Session = Depends(get_db)):
    s = db.get(Settings, 1)
    if not s:
        raise HTTPException(status_code=500, detail="设置未初始化")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return SettingsOut.model_validate(s)


@router.get("/profile", response_model=ProfileOut)
def get_profile(db: Session = Depends(get_db)):
    p = db.get(UserProfile, 1)
    if not p:
        raise HTTPException(status_code=500, detail="账号信息未初始化")
    return ProfileOut.model_validate(p)


@router.patch("/profile", response_model=ProfileOut)
def update_profile(payload: ProfileUpdate, db: Session = Depends(get_db)):
    p = db.get(UserProfile, 1)
    if not p:
        raise HTTPException(status_code=500, detail="账号信息未初始化")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return ProfileOut.model_validate(p)

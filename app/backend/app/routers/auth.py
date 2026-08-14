from fastapi import APIRouter, Depends

from app.deps import require_token

router = APIRouter(tags=["auth"])


@router.post("/auth/verify")
def verify_token(_: None = Depends(require_token)):
    return {"ok": True}

from fastapi import APIRouter

router = APIRouter(tags=["auth"])


@router.post("/auth/verify")
def verify_token():
    return {"ok": True}

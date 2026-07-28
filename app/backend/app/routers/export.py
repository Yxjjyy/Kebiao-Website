from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.deps import get_db
from app.services.excel_service import generate_xlsx

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/xlsx")
def export_xlsx(
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    db: Session = Depends(get_db),
):
    data = generate_xlsx(db, from_date, to_date)
    filename = f"kebiao_{from_date.isoformat()}_{to_date.isoformat()}.xlsx"
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

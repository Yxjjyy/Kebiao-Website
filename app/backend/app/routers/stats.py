from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.deps import get_db
from app.schemas.stats import (
    ComparisonStats,
    LeaveItem,
    RangeStats,
    StudentStatsRow,
    TodayStats,
)
from app.services import stats_service

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/today", response_model=TodayStats)
def stats_today(db: Session = Depends(get_db)):
    return stats_service.today_summary(db)


@router.get("/range", response_model=RangeStats)
def stats_range(
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    granularity: str = Query("day", pattern="^(day|week|month)$"),
    db: Session = Depends(get_db),
):
    return stats_service.range_stats(
        db, from_date=from_date, to_date=to_date, granularity=granularity
    )


@router.get("/students", response_model=list[StudentStatsRow])
def stats_students(
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    db: Session = Depends(get_db),
):
    return stats_service.student_ranking(db, from_date=from_date, to_date=to_date)


@router.get("/leave", response_model=list[LeaveItem])
def stats_leave(
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    db: Session = Depends(get_db),
):
    return stats_service.leave_list(db, from_date=from_date, to_date=to_date)


@router.get("/comparison", response_model=ComparisonStats)
def stats_comparison(
    period: str = Query("week", pattern="^(week|month)$"),
    db: Session = Depends(get_db),
):
    return stats_service.comparison(db, period)

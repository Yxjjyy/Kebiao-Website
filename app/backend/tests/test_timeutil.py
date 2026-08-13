from datetime import date, datetime, timezone

from app import timeutil


def test_business_now_resolves_timezone_per_call():
    instant = datetime(2026, 8, 13, 16, 30, tzinfo=timezone.utc)

    assert timeutil.now("UTC", instant=instant).date() == date(2026, 8, 13)
    assert timeutil.now("Asia/Shanghai", instant=instant).date() == date(2026, 8, 14)
    assert timeutil.today("Asia/Shanghai", instant=instant) == date(2026, 8, 14)


def test_week_boundaries_support_monday_and_sunday_start():
    value = date(2026, 1, 1)
    assert timeutil.week_start(value, week_starts_on=1) == date(2025, 12, 29)
    assert timeutil.week_end(value, week_starts_on=1) == date(2026, 1, 4)
    assert timeutil.week_start(value, week_starts_on=0) == date(2025, 12, 28)
    assert timeutil.week_end(value, week_starts_on=0) == date(2026, 1, 3)


def test_month_end_handles_leap_year_and_year_boundary():
    assert timeutil.month_end(date(2024, 2, 10)) == date(2024, 2, 29)
    assert timeutil.month_end(date(2026, 12, 10)) == date(2026, 12, 31)

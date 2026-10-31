"""Рабочее время магазина: сложение и разность в рабочих минутах.

Рабочая минута — минута внутри рабочих часов магазина в рабочий день, который
не праздник. Часы, дни и праздники считаются по местному времени магазина.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .models import Store


def to_local(moment: datetime, store: Store) -> datetime:
    return moment.astimezone(timezone(timedelta(hours=store.utc_offset)))


def is_working_day(day, store: Store) -> bool:
    return day.weekday() in store.workdays and day not in store.holidays


def _day_bounds(local_day: datetime, store: Store) -> tuple[datetime, datetime]:
    start = local_day.replace(hour=store.work_start, minute=0, second=0, microsecond=0)
    end = local_day.replace(hour=store.work_end, minute=0, second=0, microsecond=0)
    return start, end


def business_minutes_between(start: datetime, end: datetime, store: Store) -> int:
    """Сколько полных рабочих минут прошло от start до end (0, если end раньше)."""
    if end <= start:
        return 0
    cursor = to_local(start, store)
    finish = to_local(end, store)
    total = timedelta()
    while cursor < finish:
        day_start, day_end = _day_bounds(cursor, store)
        if is_working_day(cursor.date(), store):
            lo = max(cursor, day_start)
            hi = min(finish, day_end)
            if hi > lo:
                total += hi - lo
        cursor = (cursor + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return int(total.total_seconds() // 60)


def add_business_minutes(start: datetime, minutes: int, store: Store) -> datetime:
    """Момент, когда от start пройдёт minutes рабочих минут. Ответ в UTC."""
    cursor = to_local(start, store)
    left = timedelta(minutes=minutes)
    while True:
        day_start, day_end = _day_bounds(cursor, store)
        if is_working_day(cursor.date(), store) and cursor < day_end:
            lo = max(cursor, day_start)
            if lo + left <= day_end:
                return (lo + left).astimezone(timezone.utc)
            left -= day_end - lo
        cursor = (cursor + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

from datetime import date, datetime, timedelta, timezone

from helpdesk.models import Store

MSK = timezone(timedelta(hours=3))


def msk(y, m, d, hh=0, mm=0):
    """Момент по московскому времени, переведённый в UTC."""
    return datetime(y, m, d, hh, mm, tzinfo=MSK).astimezone(timezone.utc)


def store(**kw):
    base = dict(id="s1", name="Пример", holidays=frozenset({date(2026, 11, 4)}))
    base.update(kw)
    return Store(**base)

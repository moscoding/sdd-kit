"""Приёмка фичи «Эскалация по SLA» (практика 9 курса «Разработка по спекам»).

Запуск из корня вашего проекта helpdesk:

    python3 ../sdd-kit/escalation/checks/check_escalation.py

Проверка импортирует helpdesk.escalation.check_escalation из текущей папки и
прогоняет сценарии брифа. Ожидаемые значения она не печатает. Когда пройдены
все сценарии, она печатает код практики: его вводят в уроке.
"""
from __future__ import annotations

import hashlib
import importlib
import pathlib
import sys
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "kitlib"))
from check import Check, Result, Stop  # noqa: E402

MSK = timezone(timedelta(hours=3))


def msk(y, m, d, hh=0, mm=0):
    return datetime(y, m, d, hh, mm, tzinfo=MSK).astimezone(timezone.utc)


check = Check("Приёмка фичи «Эскалация по SLA»")
env = {}


@check.before
def load():
    sys.path.insert(0, str(pathlib.Path.cwd()))
    if not (pathlib.Path.cwd() / "helpdesk" / "models.py").exists():
        raise Stop("Не нашли helpdesk/models.py в текущей папке.", "Запустите проверку из корня проекта helpdesk.")
    try:
        models = importlib.import_module("helpdesk.models")
        module = importlib.import_module("helpdesk.escalation")
    except ModuleNotFoundError as exc:
        raise Stop(f"Не импортируется модуль: {exc.name}.", "Фича живёт в helpdesk/escalation.py, функция — check_escalation.")
    if not hasattr(module, "check_escalation"):
        raise Stop("В helpdesk/escalation.py нет функции check_escalation(ticket, store, now).")
    env.update(models=models, fn=module.check_escalation)


def store(**kw):
    base = dict(id="s1", name="Пример", holidays=frozenset({date(2026, 11, 4)}))
    base.update(kw)
    return env["models"].Store(**base)


def ticket(priority="normal", created=None, **kw):
    base = dict(id="t1", store_id="s1", priority=priority, status="open", created_at=created or msk(2026, 11, 2, 10))
    base.update(kw)
    return env["models"].Ticket(**base)


def run(t, s, now):
    got = env["fn"](t, s, now)
    if got is None:
        return None
    return (got.level, tuple(got.notify), got.priority)


SCENARIOS = []


def scenario(code, title, hint):
    def wrap(fn):
        SCENARIOS.append(code)

        @check.criterion(f"{code} {title}")
        def _():
            ok = fn()
            return Result(ok, pass_=f"{code} {title}", fail=f"{code} {title}", hint=hint)
        return fn
    return wrap


@scenario("E1", "до 80% срока эскалации нет", "до 80% срока функция возвращает None.")
def _():
    return run(ticket(), store(), msk(2026, 11, 2, 16, 23)) is None


@scenario("E2", "на 80% срока — первый уровень, сообщаем старшему смены", "проверьте границу: 80% срока — уже эскалация.")
def _():
    return run(ticket(), store(), msk(2026, 11, 2, 16, 24)) == (1, ("lead",), "normal")


@scenario("E3", "срок истёк — второй уровень и приоритет на ступень выше", "кому сообщают на втором уровне и как меняется приоритет?")
def _():
    return run(ticket(), store(), msk(2026, 11, 2, 18)) == (2, ("lead", "head"), "high")


@scenario("E4", "urgent выше не поднимается", "у приоритета urgent следующей ступени нет.")
def _():
    return run(ticket("urgent"), store(), msk(2026, 11, 2, 11)) == (2, ("lead", "head"), "urgent")


@scenario("E5", "срок считается в рабочих минутах, ночь и выходные не в счёт", "время между закрытием и открытием магазина в срок не входит.")
def _():
    s = store()
    friday = ticket(created=msk(2026, 11, 6, 17))
    return run(friday, s, msk(2026, 11, 9, 10)) is None and run(friday, s, msk(2026, 11, 9, 15, 24)) == (1, ("lead",), "normal")


@scenario("E6", "праздник магазина — нерабочий день", "праздники магазина лежат в store.holidays.")
def _():
    t = ticket("high", created=msk(2026, 11, 3, 16))
    return run(t, store(), msk(2026, 11, 5, 9, 30)) is None and run(t, store(), msk(2026, 11, 5, 11)) == (2, ("lead", "head"), "urgent")


@scenario("E7", "часы магазина — по его часовому поясу", "рабочие часы считаются по местному времени магазина: store.utc_offset.")
def _():
    nsk = store(utc_offset=7)
    t = ticket("urgent", created=msk(2026, 11, 2, 13, 30))   # 17:30 в Новосибирске
    return run(t, nsk, msk(2026, 11, 2, 15)) is None and run(t, nsk, msk(2026, 11, 3, 5, 30)) == (2, ("lead", "head"), "urgent")


@scenario("E8", "тикет, который ждёт покупателя или закрыт, не эскалируется", "эскалируются только тикеты в статусах new и open.")
def _():
    late = msk(2026, 11, 3, 18)
    return all(run(ticket(status=st), store(), late) is None for st in ("waiting_customer", "resolved", "closed")) \
        and run(ticket(status="new"), store(), late) is not None


@scenario("E9", "после первого ответа эскалации нет", "тикет с first_response_at уже получил ответ.")
def _():
    return run(ticket(first_response_at=msk(2026, 11, 2, 12)), store(), msk(2026, 11, 3, 18)) is None


@scenario("E10", "уровень, который уже был, не повторяется", "сравните новый уровень с ticket.escalation_level.")
def _():
    s = store()
    return (run(ticket(escalation_level=1), s, msk(2026, 11, 2, 17)) is None
            and run(ticket(escalation_level=1), s, msk(2026, 11, 2, 18)) == (2, ("lead", "head"), "high")
            and run(ticket(escalation_level=2), s, msk(2026, 11, 3, 18)) is None)


@scenario("E11", "VIP-магазин: на втором уровне сообщаем аккаунт-менеджеру", "у VIP-магазина store.vip == True.")
def _():
    vip = store(vip=True)
    return (run(ticket(), vip, msk(2026, 11, 2, 18)) == (2, ("lead", "head", "account_manager"), "high")
            and run(ticket(), vip, msk(2026, 11, 2, 16, 30)) == (1, ("lead",), "normal"))


@scenario("E12", "тикет из выходного начинает отсчёт с понедельника", "тикет, созданный в субботу, ждёт с начала рабочего дня.")
def _():
    t = ticket("urgent", created=msk(2026, 11, 7, 12))
    return run(t, store(), msk(2026, 11, 9, 9, 47)) is None and run(t, store(), msk(2026, 11, 9, 9, 48)) == (1, ("lead",), "urgent")


def _code():
    digest = hashlib.sha256(("sdd-escalation-v1:" + ",".join(SCENARIOS)).encode()).hexdigest()
    return int(digest, 16) % 900000 + 100000


def _run_with_code():
    try:
        check.run()
    except SystemExit as exit_:
        if exit_.code == 0:
            print(f"Код практики: {_code()}")
        raise


if __name__ == "__main__":
    _run_with_code()

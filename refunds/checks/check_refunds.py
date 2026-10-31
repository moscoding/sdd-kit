"""Приёмка фичи «Возвраты по политике магазина» (итоговый проект курса «Разработка по спекам»).

Запуск из корня вашего проекта helpdesk:

    python3 ../sdd-kit/refunds/checks/check_refunds.py

Проверка импортирует helpdesk.refunds.decide_refund из текущей папки и
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


check = Check("Приёмка фичи «Возвраты по политике магазина»")
env = {}


@check.before
def load():
    sys.path.insert(0, str(pathlib.Path.cwd()))
    if not (pathlib.Path.cwd() / "helpdesk" / "models.py").exists():
        raise Stop("Не нашли helpdesk/models.py в текущей папке.", "Запустите проверку из корня проекта helpdesk.")
    try:
        models = importlib.import_module("helpdesk.models")
        module = importlib.import_module("helpdesk.refunds")
    except ModuleNotFoundError as exc:
        raise Stop(f"Не импортируется модуль: {exc.name}.", "Фича живёт в helpdesk/refunds.py, функция — decide_refund.")
    if not hasattr(module, "decide_refund"):
        raise Stop("В helpdesk/refunds.py нет функции decide_refund(request, order, policy, now).")
    env.update(m=models, fn=module.decide_refund)


DELIVERED = msk(2026, 11, 2, 12)


def order(refunded=0, delivered=DELIVERED, shipping=39_000):
    m = env["m"]
    items = (
        m.OrderItem("kettle", "appliances", 459_000, 1),
        m.OrderItem("mug", "kitchen", 69_000, 4),
        m.OrderItem("ebook", "digital", 49_000, 1),
        m.OrderItem("brush", "hygiene", 29_000, 2),
    )
    return m.Order("o1", "s1", items, shipping, delivered, refunded)


def request(items, reason="changed_mind", created=None):
    return env["m"].RefundRequest("o1", tuple(items), reason, created or msk(2026, 11, 5, 10))


def run(req, o=None, policy=None, now=None):
    p = policy or env["m"].RefundPolicy()
    got = env["fn"](req, o or order(), p, now or msk(2026, 11, 5, 10))
    return (got.status, got.amount, got.reason if got.status == "rejected" else "")


SCENARIOS = []


def scenario(code, title, hint):
    def wrap(fn):
        SCENARIOS.append(code)

        @check.criterion(f"{code} {title}")
        def _():
            return Result(fn(), pass_=f"{code} {title}", fail=f"{code} {title}", hint=hint)
        return fn
    return wrap


@scenario("R1", "обычный возврат в срок одобряется на сумму товаров", "сумма — цена за штуку × количество по каждой позиции, в копейках.")
def _():
    return run(request([("mug", 2)])) == ("approved", 138_000, "")


@scenario("R2", "заказ не доставлен — отказ not_delivered", "без delivered_at возврат не рассматривают.")
def _():
    return run(request([("mug", 1)]), order(delivered=None)) == ("rejected", 0, "not_delivered")


@scenario("R3", "чужой товар или лишнее количество — отказ bad_items", "товар из заявки должен быть в заказе, количество — от 1 до заказанного.")
def _():
    return (run(request([("mug", 5)])) == ("rejected", 0, "bad_items")
            and run(request([("phone", 1)])) == ("rejected", 0, "bad_items")
            and run(request([("mug", 0)])) == ("rejected", 0, "bad_items"))


@scenario("R4", "передумал: 14 дней после доставки включительно", "окно считается от delivered_at; ровно 14 дней — ещё можно.")
def _():
    edge = DELIVERED + timedelta(days=14)
    return (run(request([("mug", 1)]), now=edge) == ("approved", 69_000, "")
            and run(request([("mug", 1)]), now=edge + timedelta(minutes=1)) == ("rejected", 0, "window_expired"))


@scenario("R5", "брак и пересорт — своё окно, 365 дней", "у брака и пересорта окно policy.defect_window_days.")
def _():
    late = DELIVERED + timedelta(days=200)
    return (run(request([("mug", 1)], "defect"), now=late) == ("approved", 108_000, "")
            and run(request([("mug", 1)], "changed_mind"), now=late) == ("rejected", 0, "window_expired"))


@scenario("R6", "цифровые товары и гигиену по желанию не возвращают", "категории из policy.non_returnable не возвращают по причине changed_mind.")
def _():
    return (run(request([("ebook", 1)])) == ("rejected", 0, "non_returnable")
            and run(request([("mug", 1), ("brush", 1)])) == ("rejected", 0, "non_returnable"))


@scenario("R7", "брак у невозвратной категории возвращают", "запрет non_returnable касается только changed_mind.")
def _():
    return run(request([("brush", 1)], "defect")) == ("approved", 68_000, "")


@scenario("R8", "доставку возвращают при браке и пересорте, если это первый возврат", "доставка — order.shipping, только при order.refunded == 0.")
def _():
    return (run(request([("kettle", 1)], "wrong_item")) == ("approved", 498_000, "")
            and run(request([("mug", 1)], "defect"), order(refunded=69_000)) == ("approved", 69_000, "")
            and run(request([("mug", 1)], "changed_mind")) == ("approved", 69_000, ""))


@scenario("R9", "больше оплаченного не возвращают — отказ exceeds_paid", "сравните сумму с оплаченным за заказ минус order.refunded.")
def _():
    return run(request([("kettle", 1)]), order(refunded=500_000)) == ("rejected", 0, "exceeds_paid")


@scenario("R10", "от порога сумма ждёт согласования старшего", "порог policy.approval_threshold, ровно на пороге — уже согласование.")
def _():
    policy = env["m"].RefundPolicy(approval_threshold=459_000)
    return (run(request([("kettle", 1)]), policy=policy) == ("needs_approval", 459_000, "")
            and run(request([("mug", 4)]), policy=policy) == ("approved", 276_000, ""))


@scenario("R11", "порядок отказов: сначала доставка, потом позиции, срок и категория", "проверки идут в порядке брифа: первая сработавшая даёт код.")
def _():
    late = DELIVERED + timedelta(days=30)
    return (run(request([("phone", 1)]), order(delivered=None)) == ("rejected", 0, "not_delivered")
            and run(request([("phone", 1)]), now=late) == ("rejected", 0, "bad_items")
            and run(request([("ebook", 1)]), now=late) == ("rejected", 0, "window_expired"))


@scenario("R12", "окно магазина берётся из его политики", "длины окон лежат в policy, а не в константах кода.")
def _():
    short = env["m"].RefundPolicy(window_days=7)
    now = DELIVERED + timedelta(days=10)
    return run(request([("mug", 1)]), policy=short, now=now) == ("rejected", 0, "window_expired")


def _code():
    digest = hashlib.sha256(("sdd-refunds-v1:" + ",".join(SCENARIOS)).encode()).hexdigest()
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

"""Приёмка изменения «Правило SALE в старом модуле» (модуль 9 курса «Разработка по спекам»).

Запуск из корня вашего проекта helpdesk:

    python3 ../sdd-kit/legacy-sale/checks/check_legacy_sale.py

Проверка импортирует helpdesk.billing.legacy.legacy_refund из текущей папки и
прогоняет сценарии брифа и поведение, которое должно сохраниться. Ожидаемые значения она не печатает. Когда пройдены
все сценарии, она печатает код практики: его вводят в уроке.
"""
from __future__ import annotations

import hashlib
import importlib
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "kitlib"))
from check import Check, Result, Stop  # noqa: E402



check = Check("Приёмка изменения «Правило SALE в старом модуле»")
env = {}


@check.before
def load():
    sys.path.insert(0, str(pathlib.Path.cwd()))
    if not (pathlib.Path.cwd() / "helpdesk" / "billing" / "legacy.py").exists():
        raise Stop("Не нашли helpdesk/billing/legacy.py в текущей папке.", "Запустите проверку из корня проекта helpdesk и обновите стартовый проект из sdd-kit.")
    module = importlib.import_module("helpdesk.billing.legacy")
    if not hasattr(module, "legacy_refund"):
        raise Stop("В helpdesk/billing/legacy.py нет функции legacy_refund.")
    env["fn"] = module.legacy_refund


def f(*args, **kw):
    return env["fn"](*args, **kw)


SCENARIOS = []


def scenario(code, title, hint):
    def wrap(fn):
        SCENARIOS.append(code)

        @check.criterion(f"{code} {title}")
        def _():
            return Result(fn(), pass_=f"{code} {title}", fail=f"{code} {title}", hint=hint)
        return fn
    return wrap


@scenario("S1", "SALE при браке: полная сумма товаров без доставки", "по новому правилу SALE доставку не возвращают даже при браке.")
def _():
    return f(1385, 390, 3, "defect", "SALE") == 1380


@scenario("S2", "SALE, передумал: полная сумма товаров", "скидки 10% для SALE больше нет: возвращается полная сумма товаров.")
def _():
    return f(1385, 390, 3, "changed_mind", "SALE") == 1380 and f(2000, 390, 3, "changed_mind", "SALE") == 2000


@scenario("S3", "SALE при пересорте: без доставки", "правило SALE одинаково для брака и пересорта.")
def _():
    return f(4590, 390, 30, "wrong_item", "SALE") == 4590


@scenario("S4", "SALE не отменяет окно «передумал»", "окно 14 дней для «передумал» действует и для SALE.")
def _():
    return f(1385, 390, 15, "changed_mind", "SALE") == 0 and f(1385, 390, 14, "changed_mind", "SALE") == 1380


@scenario("K1", "округление вниз до десятков рублей сохранилось", "старое округление вниз — договорённость с магазинами, его не меняют.")
def _():
    return f(1389, 390, 3, "changed_mind") == 1380 and f(1381, 390, 3, "changed_mind") == 1380


@scenario("K2", "неизвестная причина по-прежнему как «передумал»", "старый код не бросает ошибку на неизвестной причине.")
def _():
    return f(1385, 390, 3, "broken") == 1380 and f(1385, 390, 20, "broken") == 0


@scenario("K3", "окно «передумал» — 14 дней включительно", "граница окна не изменилась: 14-й день ещё можно.")
def _():
    return f(1380, 390, 14, "changed_mind") == 1380 and f(1380, 390, 15, "changed_mind") == 0


@scenario("K4", "брак без SALE: товары плюс доставка, без окна", "вне акции брак возвращается с доставкой и без срока.")
def _():
    return f(1385, 390, 3, "defect") == 1770 and f(1385, 390, 400, "defect") == 1770


@scenario("K5", "потолок 50 000 ₽ сохранился, и для SALE тоже", "потолок применяется ко всем возвратам.")
def _():
    return f(60000, 390, 3, "defect") == 50000 and f(55000, 390, 3, "defect", "SALE") == 50000


@scenario("K6", "сигнатура функции не изменилась", "выгрузка для бухгалтерии вызывает legacy_refund(total, shipping, days, reason, promo=None).")
def _():
    import inspect
    params = list(inspect.signature(env["fn"]).parameters)
    return params == ["total", "shipping", "days", "reason", "promo"] and f(1000, 0, 1, "defect") == 1000


def _code():
    digest = hashlib.sha256(("sdd-legacy-sale-v1:" + ",".join(SCENARIOS)).encode()).hexdigest()
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

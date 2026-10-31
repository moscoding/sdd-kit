"""Модели сервиса поддержки. Все моменты времени — datetime с часовым поясом UTC."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

PRIORITIES = ("low", "normal", "high", "urgent")
STATUSES = ("new", "open", "waiting_customer", "resolved", "closed")


@dataclass(frozen=True)
class Store:
    """Магазин-клиент. Рабочие часы и праздники — по местному времени магазина."""

    id: str
    name: str
    utc_offset: int = 3                 # часы от UTC: Москва +3, Новосибирск +7
    work_start: int = 9                 # первый рабочий час, включительно
    work_end: int = 18                  # конец рабочего дня, не включительно
    workdays: frozenset[int] = frozenset({0, 1, 2, 3, 4})   # понедельник = 0
    holidays: frozenset[date] = frozenset()
    vip: bool = False


@dataclass
class Ticket:
    id: str
    store_id: str
    priority: str                       # один из PRIORITIES
    status: str                         # один из STATUSES
    created_at: datetime
    first_response_at: datetime | None = None
    escalation_level: int = 0           # 0 — эскалаций не было
    assignee: str | None = None
    language: str = "ru"


@dataclass(frozen=True)
class Operator:
    id: str
    shift_start: datetime
    shift_end: datetime                 # не включительно
    languages: frozenset[str] = frozenset({"ru"})
    max_open: int = 5                   # сколько открытых тикетов можно держать
    open_tickets: int = 0


@dataclass(frozen=True)
class Escalation:
    """Результат проверки эскалации."""

    level: int                          # 1 или 2
    notify: tuple[str, ...]             # кому сообщить: "lead", "head", "account_manager"
    priority: str                       # приоритет тикета после эскалации


@dataclass(frozen=True)
class OrderItem:
    sku: str
    category: str
    price: int                          # цена за штуку в копейках
    qty: int


@dataclass(frozen=True)
class Order:
    id: str
    store_id: str
    items: tuple[OrderItem, ...]
    shipping: int                       # стоимость доставки в копейках
    delivered_at: datetime | None = None
    refunded: int = 0                   # уже вернули по заказу, копейки


@dataclass(frozen=True)
class RefundRequest:
    order_id: str
    items: tuple[tuple[str, int], ...]  # пары (sku, количество)
    reason: str                         # "defect", "wrong_item" или "changed_mind"
    created_at: datetime


@dataclass(frozen=True)
class RefundPolicy:
    """Политика возвратов магазина."""

    window_days: int = 14
    defect_window_days: int = 365
    non_returnable: frozenset[str] = frozenset({"digital", "hygiene"})
    approval_threshold: int = 2_000_000  # от этой суммы возврат согласует старший, копейки


@dataclass(frozen=True)
class RefundDecision:
    status: str                         # "approved", "needs_approval" или "rejected"
    amount: int = 0                     # копейки; у отказа 0
    reason: str = ""                    # код причины отказа, у одобренных пусто

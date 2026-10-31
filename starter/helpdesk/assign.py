"""Автоназначение новых тикетов на операторов."""
from __future__ import annotations

from datetime import datetime

from .models import Operator, Ticket


def on_shift(operator: Operator, now: datetime) -> bool:
    return operator.shift_start <= now < operator.shift_end


def assign(tickets: list[Ticket], operators: list[Operator], now: datetime) -> dict[str, str | None]:
    """Назначает тикеты по очереди: самый старый тикет — оператору на смене с наименьшей загрузкой.

    Оператор подходит, если он на смене, знает язык тикета и у него есть место
    (open_tickets плюс уже назначенные сейчас меньше max_open). При равной
    загрузке выбирается оператор с меньшим id. Если никто не подходит, тикет
    остаётся без оператора (None).
    """
    load = {op.id: op.open_tickets for op in operators}
    result: dict[str, str | None] = {}
    for ticket in sorted(tickets, key=lambda t: (t.created_at, t.id)):
        candidates = [
            op for op in operators
            if on_shift(op, now) and ticket.language in op.languages and load[op.id] < op.max_open
        ]
        if not candidates:
            result[ticket.id] = None
            continue
        best = min(candidates, key=lambda op: (load[op.id], op.id))
        load[best.id] += 1
        result[ticket.id] = best.id
    return result

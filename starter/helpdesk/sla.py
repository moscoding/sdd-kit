"""SLA первого ответа: срок, к которому оператор должен ответить на тикет."""
from __future__ import annotations

from datetime import datetime

from .models import Store, Ticket
from .worktime import add_business_minutes, business_minutes_between

# Срок первого ответа в рабочих минутах магазина.
FIRST_RESPONSE_MINUTES = {"urgent": 60, "high": 240, "normal": 480, "low": 1440}


def first_response_due(ticket: Ticket, store: Store) -> datetime:
    """Крайний срок первого ответа, UTC."""
    return add_business_minutes(ticket.created_at, FIRST_RESPONSE_MINUTES[ticket.priority], store)


def elapsed_business_minutes(ticket: Ticket, store: Store, now: datetime) -> int:
    """Сколько рабочих минут тикет ждёт первого ответа к моменту now."""
    return business_minutes_between(ticket.created_at, now, store)

# legacy-sale

Практика модуля 9 «Правило SALE в старом модуле». Бриф и порядок работы — в уроке.

Старый расчёт — `helpdesk/billing/legacy.py`, функция `legacy_refund(total, shipping, days, reason, promo=None)`.
Проверка из папки `helpdesk`:

```bash
python3 ../sdd-kit/legacy-sale/checks/check_legacy_sale.py
```

Она проверяет новое правило SALE и то, что остальное поведение старого расчёта не изменилось.

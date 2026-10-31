# escalation

Практика модуля 6 «Эскалация по SLA». Бриф продакта, вопросы к нему и порядок работы — в уроке.

Фича живёт в `helpdesk/escalation.py`: функция `check_escalation(ticket, store, now)` возвращает
`Escalation` из `helpdesk/models.py` или `None`. Проверка из папки `helpdesk`:

```bash
python3 ../sdd-kit/escalation/checks/check_escalation.py
```

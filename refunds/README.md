# refunds

Итоговый проект «Возвраты по политике магазина». Бриф, критерии и порядок работы — в уроке.

Фича живёт в `helpdesk/refunds.py`: функция `decide_refund(request, order, policy, now)` возвращает
`RefundDecision` из `helpdesk/models.py`. Проверка из папки `helpdesk`:

```bash
python3 ../sdd-kit/refunds/checks/check_refunds.py
```

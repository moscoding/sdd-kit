# Расчёт суммы возврата, 2021 год. Суммы в рублях, целые. days — дней после доставки.
# Используется в выгрузке для бухгалтерии магазинов. Тестов нет.


def legacy_refund(total, shipping, days, reason, promo=None):
    if reason not in ("defect", "changed_mind", "wrong_item"):
        reason = "changed_mind"
    if reason == "changed_mind" and days > 14:
        return 0
    amount = total
    if reason != "changed_mind":
        amount += shipping
    if promo == "SALE":
        amount = amount * 9 // 10
    if amount > 50000:
        amount = 50000
    return amount - amount % 10

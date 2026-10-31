import unittest

from helpdesk.worktime import add_business_minutes, business_minutes_between
from tests.helpers import msk, store


class WorktimeTest(unittest.TestCase):
    def test_inside_one_day(self):
        # Понедельник 2 ноября 2026, 10:00 → 12:30 по Москве
        self.assertEqual(business_minutes_between(msk(2026, 11, 2, 10), msk(2026, 11, 2, 12, 30), store()), 150)

    def test_night_does_not_count(self):
        self.assertEqual(business_minutes_between(msk(2026, 11, 2, 17), msk(2026, 11, 3, 10), store()), 120)

    def test_holiday_is_skipped(self):
        # 4 ноября — праздник: со вторника 17:00 до четверга 10:00 — час во вторник и час в четверг
        self.assertEqual(business_minutes_between(msk(2026, 11, 3, 17), msk(2026, 11, 5, 10), store()), 120)

    def test_add_over_weekend(self):
        # Пятница 6 ноября 17:30 + 60 минут → понедельник 9 ноября 9:30
        self.assertEqual(add_business_minutes(msk(2026, 11, 6, 17, 30), 60, store()), msk(2026, 11, 9, 9, 30))

    def test_start_before_opening(self):
        self.assertEqual(add_business_minutes(msk(2026, 11, 2, 7), 30, store()), msk(2026, 11, 2, 9, 30))

    def test_other_time_zone(self):
        nsk = store(utc_offset=7)
        # 05:00 по Москве = 09:00 в Новосибирске: начало рабочего дня магазина
        self.assertEqual(add_business_minutes(msk(2026, 11, 2, 5), 60, nsk), msk(2026, 11, 2, 6))


if __name__ == "__main__":
    unittest.main()

import unittest

from helpdesk.models import Ticket
from helpdesk.sla import elapsed_business_minutes, first_response_due
from tests.helpers import msk, store


def ticket(priority="normal", created=None):
    return Ticket(id="t1", store_id="s1", priority=priority, status="new", created_at=created or msk(2026, 11, 2, 10))


class SlaTest(unittest.TestCase):
    def test_normal_is_eight_working_hours(self):
        # Понедельник 11:00 + 8 рабочих часов: 7 часов в понедельник и час во вторник → вторник 10:00
        self.assertEqual(first_response_due(ticket(created=msk(2026, 11, 2, 11)), store()), msk(2026, 11, 3, 10))

    def test_deadline_at_closing_time(self):
        # Понедельник 10:00 + 8 рабочих часов ровно до конца дня → понедельник 18:00, а не вторник 9:00
        self.assertEqual(first_response_due(ticket(), store()), msk(2026, 11, 2, 18))

    def test_urgent_is_one_hour(self):
        self.assertEqual(first_response_due(ticket("urgent"), store()), msk(2026, 11, 2, 11))

    def test_elapsed(self):
        self.assertEqual(elapsed_business_minutes(ticket(), store(), msk(2026, 11, 2, 11, 15)), 75)


if __name__ == "__main__":
    unittest.main()

import unittest

from helpdesk.assign import assign
from helpdesk.models import Operator, Ticket
from tests.helpers import msk


def op(id, start=8, end=20, **kw):
    return Operator(id=id, shift_start=msk(2026, 11, 2, start), shift_end=msk(2026, 11, 2, end), **kw)


def t(id, minute=0, language="ru"):
    return Ticket(id=id, store_id="s1", priority="normal", status="new", created_at=msk(2026, 11, 2, 10, minute), language=language)


class AssignTest(unittest.TestCase):
    def test_least_loaded_operator(self):
        result = assign([t("a")], [op("o1", open_tickets=3), op("o2", open_tickets=1)], msk(2026, 11, 2, 12))
        self.assertEqual(result, {"a": "o2"})

    def test_off_shift_operator_is_skipped(self):
        result = assign([t("a")], [op("o1", start=13, end=21)], msk(2026, 11, 2, 12))
        self.assertEqual(result, {"a": None})

    def test_language(self):
        result = assign([t("a", language="kk")], [op("o1"), op("o2", languages=frozenset({"ru", "kk"}))], msk(2026, 11, 2, 12))
        self.assertEqual(result, {"a": "o2"})


if __name__ == "__main__":
    unittest.main()

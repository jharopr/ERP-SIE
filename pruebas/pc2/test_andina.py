"""Comprueba que la calibración no convierta datos faltantes en promesas."""
import unittest
from calibrar_andina import calibrate


class AndinaTests(unittest.TestCase):
    def test_known_quantities_reconcile_without_inventing_dates_or_approval(self):
        result = calibrate()
        facts = result["facts"]
        self.assertEqual(facts["available_quantity"] + facts["replenishment_quantity"], facts["requested_quantity"])
        self.assertIsNone(result["unknown"]["discount_limit"])
        self.assertIsNone(result["unknown"]["authorized_approver"])
        self.assertIsNone(result["scenarios"][1]["promised_date"])
        self.assertFalse(result["scenarios"][2]["invoice_issued"])
        self.assertFalse(result["scenarios"][3]["opportunity_lost"])

    def test_inconsistent_partial_plan_is_rejected(self):
        for values in [(1000, 650, 300), (0, 0, 0), (1000, -1, 1001), (1000, 650.5, 349.5)]:
            with self.subTest(values=values), self.assertRaises(ValueError):
                calibrate(*values)

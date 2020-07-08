from django.test import TestCase

from ducatus_exchange.lottery.api import LotteryRegister
from ducatus_exchange.payments.models import Payment
from ducatus_exchange.consts import DECIMALS


class LotteryTest(TestCase):
    def setUp(self):
        self.usd_prices = {
            'DUC': 0.05,
            'DUCX': 0.5,
            'ETH': 241.2,
            'BTC': 9285.74,
        }
        self.payment = Payment()

    def test_get_tickets_amount(self):
        self.assertEqual(LotteryRegister(Payment()).get_tickets_amount(usd_amount=10), 1)
        self.assertEqual(LotteryRegister(Payment()).get_tickets_amount(usd_amount=50), 6)
        self.assertEqual(LotteryRegister(Payment()).get_tickets_amount(usd_amount=100), 13)
        self.assertEqual(LotteryRegister(Payment()).get_tickets_amount(usd_amount=500), 70)
        self.assertEqual(LotteryRegister(Payment()).get_tickets_amount(usd_amount=1000), 150)
        self.assertEqual(LotteryRegister(Payment()).get_tickets_amount(usd_amount=2000), 150)
        self.assertEqual(LotteryRegister(Payment()).get_tickets_amount(usd_amount=5), 0)
        self.assertEqual(LotteryRegister(Payment()).get_tickets_amount(usd_amount=0), 0)
        self.assertEqual(LotteryRegister(Payment()).get_tickets_amount(usd_amount=1000), 150)
        self.assertEqual(LotteryRegister(Payment()).get_tickets_amount(usd_amount=9), 0)
        self.assertEqual(LotteryRegister(Payment()).get_tickets_amount(usd_amount=9.7), 1)
        self.assertEqual(LotteryRegister(Payment()).get_tickets_amount(usd_amount=49), 6)

    def test_get_usd_amount(self):
        usd_prices = {
            'DUCX': 0.5,
            'ETH': 241.2,
            'BTC': 9285,
        }

        self.assertAlmostEqual(
            LotteryRegister(Payment(currency='DUCX', original_amount=200 * DECIMALS['DUCX'])).get_usd_amount(
                usd_prices=usd_prices), 100, places=3)
        self.assertAlmostEqual(
            LotteryRegister(Payment(currency='ETH', original_amount=2 * DECIMALS['ETH'])).get_usd_amount(
                usd_prices=usd_prices), 482.4, places=3)
        self.assertAlmostEqual(
            LotteryRegister(Payment(currency='BTC', original_amount=0.05 * DECIMALS['BTC'])).get_usd_amount(
                usd_prices=usd_prices), 464.25, places=3)
        self.assertAlmostEqual(
            LotteryRegister(Payment(currency='DUCX', original_amount=0 * DECIMALS['DUCX'])).get_usd_amount(
                usd_prices=usd_prices), 0, places=3)
        self.assertAlmostEqual(
            LotteryRegister(Payment(currency='ETH', original_amount=0 * DECIMALS['ETH'])).get_usd_amount(
                usd_prices=usd_prices), 0, places=3)
        self.assertAlmostEqual(
            LotteryRegister(Payment(currency='BTC', original_amount=0 * DECIMALS['BTC'])).get_usd_amount(
                usd_prices=usd_prices), 0, places=3)

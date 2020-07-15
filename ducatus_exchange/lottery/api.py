from django.utils import timezone

from ducatus_exchange.rates.serializers import get_usd_prices
from ducatus_exchange.lottery.models import Lottery, LotteryPlayer
from ducatus_exchange.transfers.models import DucatusTransfer
from ducatus_exchange.consts import TICKETS_FOR_USD, DECIMALS, RATES_PRECISION


class LotteryRegister:

    def __init__(self, transfer: DucatusTransfer):
        self.transfer = transfer
        self.payment = transfer.payment

    def try_register_to_lotteries(self):
        active_lotteries = self.get_active_lotteries()
        for lottery in active_lotteries:
            self.register_to_lottery(lottery)

    def get_active_lotteries(self):
        active_lotteries = Lottery.objects.filter(ended=False, started_at__lt=timezone.now().timestamp())
        return active_lotteries

    def register_to_lottery(self, lottery):
        usd_prices = get_usd_prices()
        usd_amount = self.get_usd_amount(usd_prices)
        tickets_amount = self.get_tickets_amount(usd_amount)
        if not tickets_amount:
            return

        lottery_player = LotteryPlayer()
        lottery_player.sent_usd_amount = usd_amount
        lottery_player.tickets_amount = tickets_amount
        lottery_player.received_duc_amount = self.payment.sent_amount
        lottery_player.user = self.payment.exchange_request.user
        lottery_player.transfer = self.transfer
        lottery_player.lottery = lottery
        lottery_player.save()

        lottery.gave_tickets_amount += tickets_amount
        lottery.sent_duc_amount += self.payment.sent_amount
        if lottery.sent_duc_amount >= lottery.duc_amount and not lottery.filled_at:
            lottery.filled_at = int(timezone.now().timestamp())
        lottery.save()

        print(
            'address {} registered to lottery {} (id={}) with {} usd and {} tickets'.format(lottery_player.user.address,
                                                                                            lottery.name, lottery.id,
                                                                                            usd_amount, tickets_amount),
            flush=True)

    def get_tickets_amount(self, usd_amount):
        tickets_amount_result = 0
        for usd_value, tickets_amount in TICKETS_FOR_USD.items():
            if usd_amount - usd_value * RATES_PRECISION < 0:
                print('usd value', usd_amount, flush=True)
                print('tickets amount', tickets_amount_result, flush=True)
                return tickets_amount_result
            else:
                tickets_amount_result = tickets_amount
        return tickets_amount_result

    def get_usd_amount(self, usd_prices):
        currency = self.payment.currency
        amount = self.payment.original_amount
        usd_amount = usd_prices[currency] * amount / DECIMALS[currency]
        return usd_amount

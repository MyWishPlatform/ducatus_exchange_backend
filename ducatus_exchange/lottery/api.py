import sys
import traceback
from django.utils import timezone
from django.core.mail import send_mail

from ducatus_exchange.rates.serializers import get_usd_prices
from ducatus_exchange.lottery.models import Lottery, LotteryPlayer
from ducatus_exchange.transfers.models import DucatusTransfer
from ducatus_exchange.consts import TICKETS_FOR_USD, DECIMALS, RATES_PRECISION
from ducatus_exchange.email_messages import lottery_subject, lottery_text, promo_codes_text
from ducatus_exchange.settings import CONFIRMATION_FROM_EMAIL, PROMO_END_TIMESTAMP


class LotteryRegister:

    def __init__(self, transfer: DucatusTransfer):
        self.transfer = transfer
        self.payment = transfer.payment

    def try_register_to_lotteries(self):
        active_lotteries = self.get_active_lotteries()
        for lottery in active_lotteries:
            lottery_player = self.register_to_lottery(lottery)
            self.send_confirmation(lottery_player)

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

        return lottery_player

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

    def send_confirmation(self, lottery_player):
        try:
            to_email = lottery_player.transfer.payment.exchange_request.user.email
            text_body = lottery_text.format(
                tx_hash=lottery_player.transfer.tx_hash,
                tickets_amount=lottery_player.tickets_amount,
            )
            if timezone.now().timestamp() < PROMO_END_TIMESTAMP:
                lottery_player.generate_promo_codes()
                text_body += promo_codes_text.format(
                    back_office_code=lottery_player.back_office_code,
                    e_commerce_code=lottery_player.e_commerce_code
                )

            send_mail(
                lottery_subject,
                text_body,
                CONFIRMATION_FROM_EMAIL,
                [to_email],
            )

            print('conformation message sent successfully to {}'.format(to_email))
        except Exception as e:
            print('\n'.join(traceback.format_exception(*sys.exc_info())), flush=True)

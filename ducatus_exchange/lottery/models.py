import sys
import random
import string
import traceback

from django.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.fields import ArrayField
from django.core.mail import get_connection, send_mail

from ducatus_exchange.exchange_requests.models import DucatusUser
from ducatus_exchange.transfers.models import DucatusTransfer
from ducatus_exchange.consts import MAX_DIGITS
from ducatus_exchange.settings import (PROMO_CODES_LEN, WINNERS_CONGRATULATIONS_HOST, EMAIL_PORT,
                                       WINNERS_CONGRATULATIONS_FROM_EMAIL, WINNERS_CONGRATULATIONS_FROM_PASSWORD,
                                       EMAIL_USE_TLS)
from ducatus_exchange.email_messages import congratulations_html_style, congratulations_html_body


class Lottery(models.Model):
    name = models.CharField(max_length=50)
    description = JSONField()
    image = models.URLField(null=True, default=None)
    video = models.URLField(null=True, default=None)
    duc_amount = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=0, default=0)
    sent_duc_amount = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=0, default=0)
    started_at = models.BigIntegerField()
    ended = models.BooleanField(default=False)
    filled_at = models.BigIntegerField(null=True, default=None)
    gave_tickets_amount = models.IntegerField(default=0)
    winner_numbers = ArrayField(models.IntegerField())
    winner_players_ids = ArrayField(models.IntegerField())

    def send_mails_to_winners(self):
        # temporarily hardcode
        prizes = ['80% of achieved DUC sales', '68K of DUC', 'Denarius bank account']

        for i, winner_id in enumerate(self.winner_players_ids):
            winner = LotteryPlayer.objects.get(id=winner_id)
            connection = self.get_mail_connection()

            html_body = congratulations_html_style + congratulations_html_body.format(prize=prizes[i])
            try:
                send_mail(
                    'You’re a winner!',
                    '',
                    WINNERS_CONGRATULATIONS_FROM_EMAIL,
                    [winner.email],
                    connection=connection,
                    html_message=html_body,
                )
                print(f'CONGRATULATIONS message sent successfully to {winner.email}')
            except Exception as e:
                print('\n'.join(traceback.format_exception(*sys.exc_info())), flush=True)

    @staticmethod
    def get_mail_connection():
        connection = get_connection(
            host=WINNERS_CONGRATULATIONS_HOST,
            port=EMAIL_PORT,
            username=WINNERS_CONGRATULATIONS_FROM_EMAIL,
            password=WINNERS_CONGRATULATIONS_FROM_PASSWORD,
            use_tls=EMAIL_USE_TLS,
        )
        return connection


class LotteryPlayer(models.Model):
    sent_usd_amount = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=3, default=0)
    received_duc_amount = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=0, default=0)
    tickets_amount = models.IntegerField()
    user = models.ForeignKey(DucatusUser, on_delete=models.CASCADE)
    transfer = models.ForeignKey(DucatusTransfer, on_delete=models.CASCADE, null=True, default=None)
    lottery = models.ForeignKey(Lottery, on_delete=models.CASCADE)
    back_office_code = models.CharField(max_length=50, null=True, default=None)
    e_commerce_code = models.CharField(max_length=50, null=True, default=None)
    email = models.CharField(max_length=50, null=True, default=None)

    def generate_promo_codes(self):
        chars = string.ascii_letters + string.digits + '!#$%()*+,-./:;=?@[]'
        back_office_code = ''.join(random.choices(chars, k=PROMO_CODES_LEN))
        e_commerce_code = ''.join(random.choices(chars, k=PROMO_CODES_LEN))

        self.back_office_code = back_office_code
        self.e_commerce_code = e_commerce_code

        self.save()

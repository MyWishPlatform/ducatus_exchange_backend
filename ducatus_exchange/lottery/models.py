import random
import string
from django.db import models
from django.contrib.postgres.fields import JSONField

from ducatus_exchange.exchange_requests.models import DucatusUser
from ducatus_exchange.transfers.models import DucatusTransfer
from ducatus_exchange.consts import MAX_DIGITS
from ducatus_exchange.settings import PROMO_CODES_LEN


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
    winner_transfer = models.ForeignKey(DucatusTransfer, on_delete=models.SET_NULL, null=True, default=None)
    winner_user = models.ForeignKey(DucatusUser, on_delete=models.SET_NULL, null=True, default=None)


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

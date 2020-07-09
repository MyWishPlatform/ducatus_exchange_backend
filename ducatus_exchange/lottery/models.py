from django.db import models

from ducatus_exchange.exchange_requests.models import DucatusUser
from ducatus_exchange.consts import MAX_DIGITS


class Lottery(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    image = models.ImageField(upload_to='lottery_images/')
    usd_amount = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=3)
    received_usd_amount = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=3, default=0)
    started_at = models.BigIntegerField()
    ended = models.BooleanField(default=False)
    filled_at = models.BigIntegerField(null=True, default=None)


class LotteryPlayer(models.Model):
    sent_usd_amount = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=3, default=0)
    tickets_amount = models.IntegerField()
    user = models.ForeignKey(DucatusUser, on_delete=models.CASCADE)
    lottery = models.ForeignKey(Lottery, on_delete=models.CASCADE)

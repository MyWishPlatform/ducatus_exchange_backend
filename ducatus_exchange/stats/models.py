from django.db import models

from ducatus_exchange.consts import MAX_DIGITS


class StatisticsTransfer(models.Model):
    transaction_value = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=0)
    transaction_time = models.DateTimeField()
    currency = models.CharField(max_length=10)

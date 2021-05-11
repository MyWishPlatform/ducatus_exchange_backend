from django.db import models

from ducatus_exchange.consts import MAX_DIGITS


class DUC_StatisticsTransfer(models.Model):
    transaction_count = models.IntegerField()
    transaction_sum = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=0)
    transaction_time = models.DateTimeField()

class DUCX_StatisticsTransfer(models.Model):
    transaction_countX = models.IntegerField()
    transaction_sumX = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=0)
    transaction_timeX = models.DateTimeField()
    @classmethod
    def as_view(cls):
        pass

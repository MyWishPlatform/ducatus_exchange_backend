from django.db import models

from ducatus_exchange.consts import MAX_DIGITS
from ducatus_exchange.payments.models import Payment
from ducatus_exchange.exchange_requests.models import ExchangeRequest


class DucatusTransfer(models.Model):
    request = models.ForeignKey(ExchangeRequest, on_delete=models.CASCADE, null=True)
    # user_address = models.CharField(max_length=100, null=True, default='')
    tx_hash = models.CharField(max_length=100, null=True, default='')
    amount = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=0)
    # rate = models.DecimalField(max_digits=512, decimal_places=0)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE)
    state = models.CharField(max_length=50, null=True, default='')

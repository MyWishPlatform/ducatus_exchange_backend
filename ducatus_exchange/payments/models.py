from django.db import models
from django.contrib.auth.models import User

from ducatus_exchange.consts import MAX_DIGITS
from ducatus_exchange.exchange_requests.models import ExchangeRequest


class Payment(models.Model):
    """
    Model which store information about user payments

    Can link to tx_hash or Charge object, depending on what type of payment user choose
    """
    exchange_request = models.ForeignKey(ExchangeRequest, on_delete=models.CASCADE, null=True)
    tx_hash = models.CharField(max_length=100, null=True, default='')
    currency = models.CharField(max_length=50, null=True, default='')
    original_amount = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=0)
    rate = models.DecimalField(max_digits=512, decimal_places=0)
    sent_amount = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=0)
    created_date = models.DateTimeField(auto_now_add=True)
    transfer_state = models.CharField(max_length=50, null=True, default='WAITING_FOR_TRANSFER')
    collection_state = models.CharField(max_length=50, default='NOT_COLLECTED')
    collection_tx_hash = models.CharField(max_length=100, null=True, default='')

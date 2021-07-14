from django.db import models

from ducatus_exchange.consts import MAX_DIGITS
from ducatus_exchange.payments.models import Payment
from ducatus_exchange.exchange_requests.models import ExchangeRequest


class DucatusAddressBlacklist:
    duc_wallet_address = models.CharField(max_length=64, help_text='corporate wallets', default=0)
    ducx_wallet_address = models.CharField(max_length=64, help_text='corporate wallets', default=0)


class DucatusTransfer(models.Model):
    exchange_request = models.ForeignKey(ExchangeRequest, on_delete=models.CASCADE, null=True)
    tx_hash = models.CharField(max_length=100, null=True, default='')
    amount = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=0)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE)
    currency = models.CharField(max_length=25, null=True, default=None)
    state = models.CharField(max_length=50, null=True, default='')
    created_date = models.DateTimeField(auto_now_add=True)

from django.db import models
from django.contrib.auth.models import User
from ducatus_exchange.consts import MAX_DIGITS


class DucatusAddress(models.Model):
    address = models.CharField(max_length=50, unique=True)


class ExchangeRequest(models.Model):
    user = models.ForeignKey(DucatusAddress, on_delete=models.CASCADE, null=True)
    duc_address = models.CharField(max_length=50, unique=True)
    btc_address = models.CharField(max_length=50, null=True, default=None)
    eth_address = models.CharField(max_length=50, null=True, default=None)
    initial_rate_btc = models.DecimalField(max_digits=512, decimal_places=0, null=True, default=None)
    initial_rate_eth = models.DecimalField(max_digits=512, decimal_places=0, null=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)


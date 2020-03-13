from django.db import models
from django.contrib.auth.models import User
from ducatus_exchange.consts import MAX_DIGITS


class DucatusUser(models.Model):
    address = models.CharField(max_length=50, unique=True)
    platform = models.CharField(max_length=25, null=True, default=None)


class ExchangeRequest(models.Model):
    user = models.ForeignKey(DucatusUser, on_delete=models.CASCADE, null=True)
    duc_address = models.CharField(max_length=50, null=True, default=None)
    ducx_address = models.CharField(max_length=50, null=True, default=None)
    btc_address = models.CharField(max_length=50, null=True, default=None)
    eth_address = models.CharField(max_length=50, null=True, default=None)
    from_currency = models.CharField(max_length=25, null=True, default=None)
    to_currency = models.CharField(max_length=25, null=True, default=None)
    state = models.CharField(max_length=50, null=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)


from django.db import models
from django.contrib.auth.models import User
from ducatus_widget.consts import MAX_DIGITS


class DucatusAddress(models.Model):
    address = models.CharField(max_length=50, unique=True)


class ExchangeRequest(models.Model):
    user = models.ForeignKey(DucatusAddress, on_delete=models.CASCADE, null=True)
    duc_address = models.CharField(max_length=50, unique=True)
    btc_address = models.CharField(max_length=50, null=True, default=None)
    eth_address = models.CharField(max_length=50, null=True, default=None)


from django.db import models

from ducatus_exchange.exchange_requests.models import ExchangeRequest


class QuantumAccount(models.Model):
    account_id = models.IntegerField()
    address = models.CharField(max_length=50)
    access_token = models.TextField()
    token_type = models.CharField(max_length=20)
    token_expires_at = models.BigIntegerField()


class Charge(models.Model):
    exchange_request = models.ForeignKey(ExchangeRequest, on_delete=models.CASCADE, null=True)
    charge_id = models.IntegerField(unique=True)
    status = models.CharField(max_length=50)
    currency = models.CharField(max_length=10)
    amount = models.IntegerField()
    hash = models.CharField(max_length=100)
    redirect_url = models.CharField(max_length=200)
    email = models.CharField(max_length=50)
    duc_address = models.CharField(max_length=50)
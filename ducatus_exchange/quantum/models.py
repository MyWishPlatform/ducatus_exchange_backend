import random
import string

import requests
from django.db import models, IntegrityError

from ducatus_exchange.exchange_requests.models import ExchangeRequest
from ducatus_exchange.payments.models import Payment
from ducatus_exchange import settings_local

chars_for_random = string.ascii_uppercase + string.digits


def get_random_string():
    return ''.join(random.choices(chars_for_random, k=12))


class QuantumAccount(models.Model):
    account_id = models.IntegerField()
    address = models.CharField(max_length=50)
    access_token = models.TextField(null=True)
    token_type = models.CharField(max_length=20, null=True)
    token_expires_at = models.BigIntegerField(null=True)


class Charge(models.Model):
    charge_id = models.IntegerField(unique=True)
    exchange_request = models.ForeignKey(ExchangeRequest, on_delete=models.CASCADE, null=True)
    status = models.CharField(max_length=50)
    currency = models.CharField(max_length=10)
    amount = models.IntegerField()
    hash = models.CharField(max_length=100)
    redirect_url = models.CharField(max_length=200)
    email = models.CharField(max_length=50)
    duc_address = models.CharField(max_length=50)

    def create_voucher(self, usd_amount):
        domain = getattr(settings_local, 'VOUCHER_DOMAIN', None)
        api_key = getattr(settings_local, 'VOUCHER_API_KEY', None)
        if not domain or not api_key:
            raise Exception
        voucher_code = get_random_string()

        url = 'https://{}/api/v3/register_voucher/'.format(domain)
        data = {"api_key": api_key, "voucher_code": voucher_code, "usd_amount": usd_amount}
        r = requests.post(url, json=data)

        if r.status_code != 200:
            if 'voucher with this voucher code already exists' in r.content.decode():
                raise IntegrityError('voucher code')


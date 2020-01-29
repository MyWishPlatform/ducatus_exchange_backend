from django.db import models
from ducatus_exchange.consts import MAX_DIGITS


class Rate(models.Model):
    ducatus_value = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=0)
    btc_price = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=0)
    eth_price = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=0)
    datetime = models.DateTimeField(auto_now_add=True)

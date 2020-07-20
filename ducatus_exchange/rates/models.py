from django.db import models


class UsdRate(models.Model):
    btc_price = models.FloatField()
    eth_price = models.FloatField()
    datetime = models.DateTimeField(auto_now=True)

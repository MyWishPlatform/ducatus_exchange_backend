from django.db import models


class UsdRate(models.Model):
    btc_price = models.FloatField()
    eth_price = models.FloatField()
    usdc_price = models.FloatField(default=1)
    datetime = models.DateTimeField(auto_now=True)

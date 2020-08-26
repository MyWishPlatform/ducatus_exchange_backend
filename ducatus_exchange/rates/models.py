from django.db import models


class UsdRate(models.Model):
    btc_price = models.FloatField()
    eth_price = models.FloatField()
    usdc_price = models.FloatField(default=1)
    usd_price = models.FloatField(default=1)
    eur_price = models.FloatField()
    gbp_price = models.FloatField()
    chf_price = models.FloatField()
    datetime = models.DateTimeField(auto_now=True)

    def update_rates(self, BTC, ETH, USDC, USD, EUR, GBP, CHF):
        self.btc_price = BTC
        self.eth_price = ETH
        self.usdc_price = USDC
        self.usd_price = USD
        self.eur_price = EUR
        self.gbp_price = GBP
        self.chf_price = CHF


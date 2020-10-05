from rest_framework import serializers

from ducatus_exchange.rates.models import UsdRate


def get_usd_prices():
    usd_prices = {}
    rate = UsdRate.objects.first()
    usd_prices['ETH'] = rate.eth_price
    usd_prices['BTC'] = rate.btc_price
    usd_prices['USDC'] = rate.usdc_price
    usd_prices['DUC'] = 0.06
    usd_prices['DUCX'] = 0.60

    print('current rates', usd_prices, flush=True)

    return usd_prices


class DucRateSerializer(serializers.Serializer):
    BTC = serializers.FloatField()
    ETH = serializers.FloatField()
    DUCX = serializers.FloatField()


class DucxRateSerializer(serializers.Serializer):
    DUC = serializers.FloatField()


class AllRatesSerializer(serializers.Serializer):
    DUC = DucRateSerializer
    DUCX = DucxRateSerializer

    def to_representation(self, instance):
        usd_price = get_usd_prices()

        duc_prices = {currency: usd_price['DUC'] / price for currency, price in usd_price.items()}
        duc_prices.pop('DUC')

        ducx_price = {
            'DUC': usd_price['DUCX'] / usd_price['DUC']
        }

        all_rates = {
            'DUC': duc_prices,
            'DUCX': ducx_price
        }

        for rate in all_rates.values():
            for currency in rate:
                rate[currency] = '{0:.8f}'.format(rate[currency])

        return all_rates

import requests
import json

from rest_framework import serializers

from ducatus_exchange.rates.api import get_usd_prices


def request_rates(fsym, tsyms, reverse=False):
    api_url = 'https://min-api.cryptocompare.com/data/price'

    payload = {
        'fsym': fsym,
        'tsyms': tsyms
    }

    res = requests.get(api_url, params=payload)
    if res.status_code != 200:
        raise Exception('cannot get exchange rate for {}'.format(fsym))
    answer = json.loads(res.text)
    if reverse:
        answer = answer[tsyms]

    return answer


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





import requests
import json

from rest_framework import serializers


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


def get_usd_prices():
    query_tsyms = ['ETH', 'BTC']
    query_fsym = 'USD'

    usd_prices = {}
    for tsym in query_tsyms:
        usd_prices[tsym] = request_rates(tsym, query_fsym, reverse=True)

    usd_prices['DUC'] = 0.05
    usd_prices['DUCX'] = 0.50

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





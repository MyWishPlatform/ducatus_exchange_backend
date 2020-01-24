import requests
import json

from ducatus_widget.consts import DUCATUS_USD_RATE


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


def get_usd_rates():
    query_tsyms = ['ETH', 'BTC']
    query_fsym = 'USD'

    rates = request_rates(query_fsym, query_tsyms)

    usd_prices = {}
    for tsym in query_tsyms:
        usd_prices[tsym] = request_rates(tsym, query_fsym, reverse=True)

    res = {
        'rate': rates,
        'price': usd_prices
    }

    return res


def convert_to_duc(rates):
    new_rates = {}

    for item, value in rates.items():
        currencies = {'{0:.10f}'.format(value[currency] * DUCATUS_USD_RATE) for currency in value}
        new_rates[item] = currencies

    return new_rates

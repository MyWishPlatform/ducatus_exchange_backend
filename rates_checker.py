import os
import sys
import time
import json
import requests
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ducatus_exchange.settings')
import django

django.setup()

from ducatus_exchange.rates.models import UsdRate
from ducatus_exchange.settings import CRYPTOCOMPARE_API_KEY, RATES_CHECKER_TIMEOUT

api_url = 'https://min-api.cryptocompare.com/data/price'

query_tsyms = ['ETH', 'BTC']
query_fsym = 'USD'


def get_rates(fsym, tsyms, reverse=False):
    payload = {
        'fsym': fsym,
        'tsyms': tsyms,
        'api_key': CRYPTOCOMPARE_API_KEY
    }

    res = requests.get(api_url, params=payload)
    if res.status_code != 200:
        raise Exception('cannot get exchange rate for {}'.format(fsym))
    answer = json.loads(res.text)
    if reverse:
        answer = answer[tsyms]

    return answer

if __name__ == '__main__':
    while True:
        usd_prices = {}

        try:
            for tsym in query_tsyms:
                usd_prices[tsym] = get_rates(tsym, query_fsym, reverse=True)
        except Exception as e:
            print('\n'.join(traceback.format_exception(*sys.exc_info())), flush=True)
            time.sleep(RATES_CHECKER_TIMEOUT)
            continue

        print('new usd prices', usd_prices, flush=True)

        if UsdRate.objects.count() > 0:
            rate = UsdRate.objects.first()
            rate.eth_price = usd_prices['ETH']
            rate.btc_price = usd_prices['BTC']
        else:
            rate = UsdRate(eth_price=usd_prices['ETH'], btc_price=usd_prices['BTC'])
        rate.save()

        print('saved ok', flush=True)

        time.sleep(RATES_CHECKER_TIMEOUT)

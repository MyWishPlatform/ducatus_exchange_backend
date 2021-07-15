from ducatus_exchange.rates.serializers import AllRatesSerializer
from ducatus_exchange.consts import DECIMALS


def calculate_amount(original_amount, from_currency):
    to_currency = 'DUCX' if from_currency == 'DUC' else 'DUC'
    print(f'Calculating amount, original: {original_amount}, from {from_currency} to {to_currency}', flush=True)

    rates = AllRatesSerializer({})
    currency_rate = rates.data[to_currency][from_currency]

    if from_currency in ['ETH', 'DUCX', 'BTC', 'USDC']:
        value = original_amount * DECIMALS['DUC'] / DECIMALS[from_currency]
    elif from_currency == 'DUC':
        value = original_amount * DECIMALS[to_currency] / DECIMALS['DUC']
    else:
        value = original_amount

    print(f'value: {value}, rate: {currency_rate}', flush=True)
    amount = int(float(value) / float(currency_rate))

    return amount, currency_rate

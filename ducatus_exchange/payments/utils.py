from ducatus_exchange.rates.serializers import AllRatesSerializer
from ducatus_exchange.consts import DECIMALS


def calculate_amount(original_amount, from_currency):
    to_currency = 'DUCX' if from_currency == 'DUC' else 'DUC'
    print('Calculating amount, original: {orig}, from {from_curr} to {to_curr}'.format(
        orig=original_amount,
        from_curr=from_currency,
        to_curr=to_currency
        ), flush=True
    )

    rates = AllRatesSerializer({})
    currency_rate = rates.data[to_currency][from_currency]

    if from_currency in ['ETH', 'DUCX', 'BTC', 'USDC']:
        value = original_amount * DECIMALS['DUC'] / DECIMALS[from_currency]
    elif from_currency == 'DUC':
        value = original_amount * DECIMALS[to_currency] / DECIMALS['DUC']
    else:
        value = original_amount

    print('value: {value}, rate: {rate}'.format(value=value, rate=currency_rate), flush=True)
    amount = int(float(value) / float(currency_rate))

    return amount, currency_rate

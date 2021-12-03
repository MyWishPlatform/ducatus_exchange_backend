import logging

from ducatus_exchange.rates.serializers import AllRatesSerializer
from ducatus_exchange.consts import DECIMALS

logger = logging.getLogger(__name__)


def calculate_amount(original_amount, from_currency):
    to_currency = 'DUCX' if from_currency == 'DUC' else 'DUC'
    logger.info(msg=f'Calculating amount, original: {original_amount}, from {from_currency} to {to_currency}')

    rates = AllRatesSerializer({})
    currency_rate = rates.data[to_currency][from_currency]
    if from_currency in ['ETH', 'DUCX', 'BTC', 'USDC']:
        value = original_amount * DECIMALS['DUC'] / DECIMALS[from_currency]
    elif from_currency == 'DUC':
        value = original_amount * DECIMALS[to_currency] / DECIMALS['DUC']
    else:
        value = original_amount

    logger.info(msg=f'value: {value}, rate: {currency_rate}')
    amount = int(float(value) / float(currency_rate))

    return amount, currency_rate

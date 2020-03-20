from ducatus_exchange.exchange_requests.models import ExchangeRequest
from ducatus_exchange.payments.models import Payment
from ducatus_exchange.rates.serializers import AllRatesSerializer
from ducatus_exchange.transfers.api import transfer_currency
from ducatus_exchange.consts import DECIMALS
from ducatus_exchange.parity_interface import ParityInterfaceException
from ducatus_exchange.litecoin_rpc import DucatuscoreInterfaceException


class NeedRequeue(Exception):
    pass


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

    if from_currency in ['ETH', 'DUCX', 'BTC']:
        value = original_amount * DECIMALS['DUC'] / DECIMALS[from_currency]
    elif from_currency == 'DUC':
        value = original_amount * DECIMALS[to_currency] / DECIMALS['DUC']
    else:
        value = original_amount

    print('value: {value}, rate: {rate}'.format(value=value, rate=currency_rate), flush=True)
    amount = int(value / float(currency_rate))

    return amount, currency_rate


def register_payment(request_id, tx_hash, currency, amount):
    exchange_request = ExchangeRequest.objects.get(id=request_id)

    calculated_amount, rate = calculate_amount(amount, currency)
    print('amount:', calculated_amount, 'rate:', rate,  flush=True)
    payment = Payment(
        exchange_request=exchange_request,
        tx_hash=tx_hash,
        currency=currency,
        original_amount=amount,
        rate=rate,
        sent_amount=calculated_amount
    )
    # exchange_request.from_currency = currency
    # exchange_request.save()
    print(
        'PAYMENT: {amount} {curr} ({value} DUC) on rate {rate} within request {req} with TXID: {txid}'.format(
            amount=amount,
            curr=currency,
            value=calculated_amount,
            rate=rate,
            req=exchange_request.id,
            txid=tx_hash,
        ),
        flush=True
    )

    payment.save()
    print('payment ok', flush=True)
    return payment


def parse_payment_message(message):
    tx = message.get('transactionHash')
    request_id = message.get('exchangeId')
    amount = message.get('amount')
    currency = message.get('currency')
    receiving_address = message.get('address')
    print('PAYMENT:', tx, request_id, amount, currency, flush=True)
    payment = register_payment(request_id, tx, currency, amount)
    print('starting transfer', flush=True)
    try:
        transfer_currency(payment)
    except (ParityInterfaceException, DucatuscoreInterfaceException) as e:
        print('Transfer not completed, reverting payment', flush=True)
        payment.delete()
        raise NeedRequeue
    print('transfer completed', flush=True)

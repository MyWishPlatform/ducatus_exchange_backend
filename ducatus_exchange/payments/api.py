from ducatus_exchange.exchange_requests.models import ExchangeRequest
from ducatus_exchange.payments.models import Payment
from ducatus_exchange.rates.api import convert_to_duc_single, get_usd_rates
from ducatus_exchange.rates.serializers import AllRatesSerializer
from ducatus_exchange.transfers.api import transfer_currency
from ducatus_exchange.consts import DECIMALS


def convert_currency(amount, currency, saved_rate):
    if saved_rate is None:
        rate = float(convert_to_duc_single(get_usd_rates())[currency])
    else:
        rate = saved_rate
    value = amount / rate
    return {'amount': value, 'rate': rate}


def calculate_amount(original_amount, currency, saved_rate):
    value = original_amount

    if currency == 'ETH':
        value = original_amount * DECIMALS['DUC'] / DECIMALS['ETH']

    amount_to_send = convert_currency(value, currency, saved_rate)
    return {'amount': int(amount_to_send['amount']), 'rate': amount_to_send['rate']}


def register_payment(request_id, tx_hash, currency, amount):
    request = ExchangeRequest.objects.get(id=request_id)

    rates = AllRatesSerializer({})
    currency_rate = rates.data[currency]

    calculated_amount = calculate_amount(amount, currency, currency_rate)
    payment = Payment(
        exchange_request=request,
        tx_hash=tx_hash,
        currency=currency,
        original_amount=amount,
        rate=calculated_amount['rate'],
        sent_amount=calculated_amount['amount']
    )
    print(
        'PAYMENT: {amount} {curr} ({value} DUC) on rate {rate} within request {req} with TXID: {txid}'.format(
            amount=amount,
            curr=currency,
            value=calculated_amount['amount'],
            rate=calculated_amount['rate'],
            req=request.id,
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
    transfer_currency(payment)
    print('transfer completed', flush=True)

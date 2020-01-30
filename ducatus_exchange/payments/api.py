import datetime
from django.utils import timezone
from django.contrib.auth.models import User

from ducatus_exchange.exchange_requests.models import DucatusAddress, ExchangeRequest
from ducatus_exchange.payments.models import Payment
from ducatus_exchange.rates.api import convert_to_duc_single, get_usd_rates
from ducatus_exchange.transfers.api import transfer_ducatus
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
    saved_rate = None
    request = ExchangeRequest.objects.get(id=request_id)

    delta = timezone.now() - request.created_at

    if delta.seconds < 3600:
        if currency == 'BTC':
            saved_rate = ExchangeRequest.initial_rate_btc
        elif currency == 'ETH':
            saved_rate = ExchangeRequest.initial_rate_eth


    calculated_amount = calculate_amount(amount, currency, saved_rate)
    payment = Payment(
        user=request,
        tx_hash=tx_hash,
        currency=currency,
        original_amount=amount,
        rate=calculated_amount['rate'],
        sent_amount=calculated_amount['amount']
    )
    print(
        'PAYMENT: {amount} {curr} ({value} DUC) on rate {rate} from user {user} with TXID: {txid}'.format(
            amount=amount,
            curr=currency,
            value=calculated_amount['amount'],
            rate=calculated_amount['rate'],
            user=user.id,
            txid=tx_hash,
        ),
        flush=True
    )

    payment.save()
    print('payment ok', flush=True)
    return payment


def parse_payment_message(message):
    # {
    #     "status": "COMMITTED",
    #     "transactionHash": "c0963718ea4bfdf1540cfbbc46357971ac2799f45811505a6a1d8cf8c92b5906",
    #     "userAddress": "1Bwd6WKNykMtsahTSkPaJvw4m4CKXz4hPM",
    #     "amount": 600359,
    #     "currency": "BTC",
    #     "type": "payment",
    #     "success": true
    # }
    tx = message.get('transactionHash')
    user_id = message.get('userId')
    amount = message.get('amount')
    currency = message.get('currency')
    # to_address = message.get('receivingAddress')
    print('PAYMENT:', tx, user_id, amount, currency, flush=True)

    payment = register_payment(user_id, tx, currency, amount)
    print('starting transfer', flush=True)
    transfer_ducatus(payment)
    print('transfer completed', flush=True)

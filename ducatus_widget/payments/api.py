from django.contrib.auth.models import User

from ducatus_exchange.payments.models import Payment
from ducatus_exchange.rates.api import get_usd_prices, get_usd_rates, convert_to_duc_single
from ducatus_exchange.transfers.api import transfer_ducatus


DECIMALS = {
    'ETH': 10 ** 18,
    'BTC': 10 ** 8,
    'DUC': 10 ** 8,
}


def convert_currency(amount, currency):
    rate = float(convert_to_duc_single(get_usd_rates())[currency])
    value = amount / rate
    return {'amount': value, 'rate': rate}


def calculate_amount(original_amount, currency):

    value = original_amount

    if currency == 'ETH':
        value = original_amount * DECIMALS['DUC'] / DECIMALS['ETH']

    amount_to_send = convert_currency(value, currency)
    return {'amount': int(amount_to_send['amount']), 'rate': amount_to_send['rate']}


def register_payment(user_address, tx_hash, currency, amount, to_address):

    calculated_amount = calculate_amount(amount, currency)
    payment = Payment(
        # user=user,
        user_address=user_address,
        tx_hash=tx_hash,
        currency=currency,
        original_amount=amount,
        rate=calculated_amount['rate'],
        sent_amount=calculated_amount['amount']
    )
    print(
        'PAYMENT: {amount} {curr} ({value} DUC}) on rate {rate} from {addr} with TXID: {txid} to send at {to_addr}'.format(
            amount=amount,
            curr=currency,
            value=calculated_amount['amount'],
            rate=calculated_amount['rate'],
            addr=user_address,
            txid=tx_hash,
            to_addr=to_address
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
    user_address = message.get('userAddress')
    amount = message.get('amount')
    currency = message.get('currency')
    to_address = message.get('receivingAddress')
    print('PAYMENT:', tx, user_address, amount, currency, to_address, flush=True)

    payment = register_payment(user_address, tx, currency, amount, to_address)

    transfer_ducatus(payment)

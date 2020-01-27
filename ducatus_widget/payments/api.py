from django.contrib.auth.models import User

from ducatus_widget.payments.models import Payment
from ducatus_widget.rates.api import get_usd_prices, get_usd_rates, convert_to_duc_all


DECIMALS = {
    'ETH': 10 ** 18,
    'BTC': 10 ** 8,
    'DUC': 10 ** 8,
}


def convert_currency(amount, currency):
    rate = get_usd_prices()
    if currency == 'ETH':
        pass
    if currency == 'BTC':
        pass

    return {'amount': amount, 'rate': rate}


def calculate_amount(original_amount, currency):

    if currency == 'ETH':
        value = original_amount * DECIMALS['ETH'] / DECIMALS['DUC']
    else:
        value = original_amount

    amount_to_send = convert_currency(value, currency)
    return {'amount': amount_to_send['value'], 'rate': amount_to_send['rate']}


def register_payment(user_address, tx_hash, currency, amount):
    # user = User.objects.get(id=user_id)

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
        'PAYMENT REGISTERED: {value_orig} {curr} ({value} DUC}) with rate {rate} from {addr} with TXID: {txid}'.format(
            value_orig=amount,
            curr=currency,
            value=calculated_amount['amount'],
            rate=calculated_amount['rate'],
            addr=user_address,
            txid=tx_hash
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
    print('PAYMENT:', tx, user_address, amount, currency, flush=True)

    register_payment(user_address, tx, currency, amount)

import time
import datetime

from django.http import HttpRequest
from rest_framework.exceptions import ValidationError

from ducatus_exchange.payments.api import parse_payment_message
from ducatus_exchange.payments.models import Payment
from ducatus_exchange.exchange_requests.views import get_or_create_ducatus_user_and_exchange_request
from ducatus_exchange.consts import DECIMALS


def make_register(username, quantity, package, email):
    platform = 'DUC'
    currency = 'USDC'
    amount = package * DECIMALS[currency]

    address = f'voucher_{datetime.datetime.now().timestamp()}'

    ducatus_user, exchange_request = get_or_create_ducatus_user_and_exchange_request(HttpRequest(), address,
                                                                                     platform, email)

    print(ducatus_user.__dict__, flush=True)
    print(exchange_request.__dict__, flush=True)

    for _ in range(quantity):
        fake_tx_hash = f'{username}_{int(datetime.datetime.now().timestamp())}'
        message = {
            'exchangeId': exchange_request.id,
            'amount': amount,
            'currency': currency,
            'transactionHash': fake_tx_hash,
        }

        print(message, flush=True)

        parse_payment_message(message)

        payment = Payment.objects.get(tx_hash=fake_tx_hash)
        payment.collection_state = 'COLLECTED'
        payment.save()

        print(payment.__dict__, flush=True)
        time.sleep(2)


def register_payments_data(data):
    for i in data:
        try:
            make_register(i['username'], i['quantity'], i['package'], i['email'])
        except Exception as err:
            raise ValidationError(detail=f'fail with user {i["username"]}, registration stopped : {str(err)}')

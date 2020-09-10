import time
import datetime

from ducatus_exchange.payments.api import parse_payment_message
from ducatus_exchange.exchange_requests.models import DucatusUser, ExchangeRequest
from ducatus_exchange.payments.models import Payment
from ducatus_exchange.consts import DECIMALS


def make_register(username, quantity, package, address, email):
    platform = 'DUC'
    currency = 'USDC'
    amount = package * DECIMALS[currency]

    ducatus_user_filter = DucatusUser.objects.filter(address=address, platform=platform)
    user_created = False
    if not ducatus_user_filter:
        user_created = True
        ducatus_user = DucatusUser(address=address, platform=platform, email=email)
        ducatus_user.save()
    else:
        ducatus_user = ducatus_user_filter.last()
        if email:
            ducatus_user.email = email
            ducatus_user.save()

    if user_created:
        exchange_request = ExchangeRequest(user=ducatus_user)
        exchange_request.save()
        exchange_request.generate_keys()
        exchange_request.save()
    else:
        exchange_request = ExchangeRequest.objects.get(user=ducatus_user)

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
        make_register(i['username'], i['quantity'], i['package'], i['address'], i['email'])

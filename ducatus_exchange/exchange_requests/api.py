import binascii
import requests
import string
import random

from django.db import IntegrityError
from django.core.mail import send_mail

from ducatus_exchange.settings import ROOT_KEYS, BITCOIN_URLS, IS_TESTNET_PAYMENTS
from ducatus_exchange import settings_local
from ducatus_exchange.email_messages import voucher_html_body, warning_html_style
from ducatus_exchange.settings_local import CONFIRMATION_FROM_EMAIL
from ducatus_exchange.lottery.api import LotteryRegister

chars_for_random = string.ascii_uppercase + string.digits


def get_random_string():
    return ''.join(random.choices(chars_for_random, k=12))


def generate_memo(m):
    memo_str = os.urandom(8)
    m.update(memo_str)
    memo_str = binascii.hexlify(memo_str + m.digest()[0:2])
    return memo_str


def registration_btc_address(btc_address):
    requests.post(
        BITCOIN_URLS['main'],
        json={
            'method': 'importaddress',
            'params': [btc_address, btc_address, False],
            'id': 1, 'jsonrpc': '1.0'
        }
    )


def get_root_key():
    network = 'mainnet'

    if IS_TESTNET_PAYMENTS:
        network = 'testnet'

    root_pub_key = ROOT_KEYS[network]['public']

    return root_pub_key


def create_voucher(usd_amount, charge_id=None, payment_id=None):
    domain = getattr(settings_local, 'VOUCHER_DOMAIN', None)
    api_key = getattr(settings_local, 'VOUCHER_API_KEY', None)
    if not domain or not api_key:
        raise NameError(f'Cant create voucher for charge with {usd_amount} USD, '
                        'VOUCHER_DOMAIN and VOUCHER_API_KEY should be defined in settings_local.py')

    voucher_code = get_random_string()

    url = 'https://{}/api/v3/register_voucher/'.format(domain)
    data = {
        "api_key": api_key,
        "voucher_code": voucher_code,
        "usd_amount": usd_amount,
        "charge_id": charge_id,
        "payment_id": payment_id,
    }
    r = requests.post(url, json=data)

    if r.status_code != 200:
        if 'voucher with this voucher code already exists' in r.content.decode():
            raise IntegrityError('voucher code')
    return r.json()


def send_voucher_email(voucher, to_email, usd_amount):
    conn = LotteryRegister.get_mail_connection()

    html_body = voucher_html_body.format(
        voucher_code=voucher['activation_code']
    )

    send_mail(
        'Your DUC Purchase Confirmation for ${}'.format(round(usd_amount, 2)),
        '',
        CONFIRMATION_FROM_EMAIL,
        [to_email],
        connection=conn,
        html_message=warning_html_style + html_body,
    )
    print('warning message sent successfully to {}'.format(to_email))

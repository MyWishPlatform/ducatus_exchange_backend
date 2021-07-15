import os
import csv
import string
import random

import requests
from django.core.mail import send_mail
from django.db import IntegrityError
from django.utils import timezone

from ducatus_exchange.exchange_requests.models import ExchangeRequest
from ducatus_exchange.payments.models import Payment
from ducatus_exchange.rates.serializers import get_usd_prices
from ducatus_exchange.consts import DECIMALS
from ducatus_exchange.parity_interface import ParityInterfaceException
from ducatus_exchange.litecoin_rpc import DucatuscoreInterfaceException
from ducatus_exchange import settings_local
from ducatus_exchange.email_messages import voucher_html_body, warning_html_style
from ducatus_exchange.settings_local import CONFIRMATION_FROM_EMAIL
from ducatus_exchange.lottery.api import LotteryRegister
from ducatus_exchange.payments.utils import calculate_amount
from ducatus_exchange.transfers.api import transfer_currency, make_ref_transfer


class TransferException(Exception):
    pass


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
        f'PAYMENT: {amount} {currency} ({calculated_amount} DUC)'
        f' on rate {rate} within request {exchange_request.id} with TXID: {tx_hash}',
        flush=True
    )

    payment.save()
    print('payment ok', flush=True)

    return payment


def parse_payment_message(message):
    tx = message.get('transactionHash')
    if not Payment.objects.filter(tx_hash=tx).count() > 0:
        request_id = message.get('exchangeId')
        amount = message.get('amount')
        currency = message.get('currency')
        print('PAYMENT:', tx, request_id, amount, currency, flush=True)
        payment = register_payment(request_id, tx, currency, amount)

        transfer_with_handle_lottery_and_referral(payment)
    else:
        print(f'tx {tx} already registered', flush=True)


def transfer_with_handle_lottery_and_referral(payment):
    print('starting transfer', flush=True)
    try:
        if not payment.exchange_request.user.address.startswith('voucher'):
            transfer_currency(payment)
            payment.state_transfer_done()
        elif payment.exchange_request.user.platform == 'DUC':
            usd_amount = get_usd_prices()['DUC'] * int(payment.sent_amount) / DECIMALS['DUC']
            try:
                voucher = create_voucher(usd_amount, payment_id=payment.id)
            except IntegrityError as e:
                if 'voucher code' not in e.args[0]:
                    raise e
                voucher = create_voucher(usd_amount, payment_id=payment.id)
            send_voucher_email(voucher, payment.exchange_request.user.email, usd_amount)
            if payment.exchange_request.user.ref_address:
                make_ref_transfer(payment)
    except (ParityInterfaceException, DucatuscoreInterfaceException) as e:
        payment.state_transfer_error()
        payment.save()
        raise TransferException(e)
    print('transfer completed', flush=True)


def get_random_string():
    chars_for_random = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars_for_random, k=12))


def create_voucher(usd_amount, charge_id=None, payment_id=None):
    domain = getattr(settings_local, 'VOUCHER_DOMAIN', None)
    local_voucher_url = getattr(settings_local, 'VOUCHER_LOCAL_URL', None)
    api_key = getattr(settings_local, 'VOUCHER_API_KEY', None)
    if not domain or not api_key:
        raise NameError(f'Cant create voucher for charge with {usd_amount} USD, '
                        'VOUCHER_DOMAIN and VOUCHER_API_KEY should be defined in settings_local.py')

    voucher_code = get_random_string()

    url = local_voucher_url
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
        f'Your DUC Purchase Confirmation for ${round(usd_amount, 2)}',
        '',
        CONFIRMATION_FROM_EMAIL,
        [to_email],
        connection=conn,
        html_message=warning_html_style + html_body,
    )
    print(f'voucher message sent successfully to {to_email}', flush=True)


def write_payments_to_csv(outfile_path, payment_list, curr_decimals):
    with open(outfile_path, 'w') as outfile:
        writer = csv.writer(outfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
        for val in payment_list:
            writer.writerow([val.tx_hash, val.original_amount / curr_decimals])


def get_payments_statistics():
    pl = Payment.objects.filter(collection_state='NOT_COLLECTED')
    pl_eth = pl.filter(currency='ETH')
    pl_btc = pl.filter(currency='BTC')
    pl_usdc = pl.filter(currency='USDC')

    time_now = timezone.datetime.now()
    time_str = time_now.strftime('%Y_%m_%d')
    p_dir = os.path.join(os.getcwd(), 'payments_stat', time_str)
    os.mkdir(p_dir)
    print('Created directory at:', p_dir, flush=True)

    if len(pl_eth) > 0:
        print('Write ETH payment stats', flush=True)
        eth_file = os.path.join(p_dir, 'eth.csv')
        write_payments_to_csv(eth_file, pl_eth, DECIMALS['ETH'])
        print(f'Done, {len(pl_eth)} items saved to: {eth_file}', flush=True)
    else:
        print('No payments in ETH at this period', flush=True)

    if len(pl_btc) > 0:
        print('Write BTC payment stats', flush=True)
        btc_file = os.path.join(p_dir, 'btc.csv')
        write_payments_to_csv(btc_file, pl_btc, DECIMALS['BTC'])
        print(f'Done, {len(pl_btc)} items saved to: {btc_file}', flush=True)
    else:
        print('No payments in BTC at this period', flush=True)

    if len(pl_usdc) > 0:
        print('Write USDC payment stats', flush=True)
        usdc_file = os.path.join(p_dir, 'usdc.csv')
        write_payments_to_csv(usdc_file, pl_usdc, DECIMALS['USDC'])
        print(f'Done, {len(pl_usdc)} items saved to: {usdc_file}', flush=True)
    else:
        print('No payments in USDC at this period', flush=True)

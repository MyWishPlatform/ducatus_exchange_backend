import csv
import logging
import os
import random
import string
import time
import json
from sys import platform

import requests
from django.core.mail import send_mail
from django.db import IntegrityError
from django.utils import timezone
from web3 import Web3, HTTPProvider

from ducatus_exchange.exchange_requests.models import ExchangeRequest
from ducatus_exchange.payments.models import Payment
from ducatus_exchange.rates.serializers import get_usd_prices
from ducatus_exchange.consts import DECIMALS
from ducatus_exchange.parity_interface import ParityInterfaceException
from ducatus_exchange import payments, settings_local
from ducatus_exchange.consts import DAYLY_LIMIT, DECIMALS, WEEKLY_LIMIT
from ducatus_exchange.email_messages import (
    voucher_html_body,
    warning_html_style
)
from ducatus_exchange.exchange_requests.models import (
    ExchangeRequest,
    ExchangeStatus
)
from ducatus_exchange.bitcoin_api import DucatuscoreInterfaceError
from ducatus_exchange.lottery.api import LotteryRegister
from ducatus_exchange.parity_interface import (
    ParityInterface,
    ParityInterfaceException
)
from ducatus_exchange.payments.models import Payment
from ducatus_exchange.payments.utils import calculate_amount
from ducatus_exchange.rates.serializers import get_usd_prices
from ducatus_exchange.settings import MINIMAL_RETURN
from ducatus_exchange.settings_local import CONFIRMATION_FROM_EMAIL, NETWORK_SETTINGS, WALLET_API_URL, ERC20_ABI
from ducatus_exchange.transfers.api import check_limits, save_transfer, make_ref_transfer, transfer_ducatusx
from ducatus_exchange.transfers.api import save_transfer, TransferException
from web3 import Web3, HTTPProvider
from web3.exceptions import TransactionNotFound

logger = logging.getLogger(__name__)


def register_payment(request_id, tx_hash, currency, amount, from_address):
    exchange_request = ExchangeRequest.objects.get(id=request_id)

    calculated_amount, rate = calculate_amount(amount, currency)
    logger.info(msg=f'amount:{calculated_amount} rate: {rate}')
    payment = Payment(
        exchange_request=exchange_request,
        tx_hash=tx_hash,
        currency=currency,
        original_amount=amount,
        rate=rate,
        sent_amount=calculated_amount,
        from_address=from_address
    )
    logger.info(msg=(
        f'PAYMENT: {amount} {currency} from: {from_address} ({calculated_amount} DUC)'
        f' on rate {rate} within request {exchange_request.id} with TXID: {tx_hash}')
    )

    payment.save()
    logger.info(msg='payment ok')

    return payment


def parse_payment_message(message):
    tx = message.get('transactionHash')
    if not Payment.objects.filter(tx_hash=tx).count() > 0:
        request_id = message.get('exchangeId')
        amount = message.get('amount')
        currency = message.get('currency')
        from_address = message.get('fromAddress', None)
        logger.info(msg=('PAYMENT:', tx, request_id, amount, currency))
        payment = register_payment(request_id, tx, currency, amount, from_address)
        user = payment.exchange_request.user
        if user.platform == 'DUCX' and not user.address.startswith('voucher'):
            transfer_ducatusx(payment)
        elif user.platform == 'DUC':
            if user.address.startswith('voucher'):
                process_vaucher(payment)
            else:
                payment.state_transfer_queued()
                payment.save()
    else:
        logger.info(msg=f'tx {tx} already registered')

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
    logger.info(msg=f'voucher message sent successfully to {to_email}')


def process_vaucher(payment):
    try:
        usd_amount = get_usd_prices()['DUC'] * int(payment.sent_amount) / DECIMALS['DUC']
        try:
            voucher = create_voucher(usd_amount, payment_id=payment.id)
        except IntegrityError as e:
            if 'voucher code' not in e.args[0]:
                raise e
            voucher = create_voucher(usd_amount, payment_id=payment.id)
        user = payment.exchange_request.user
        send_voucher_email(voucher, user.email, usd_amount)
        if user.ref_address:
            logger.info(msg=f'payment with id: {payment.id} added to queue to send.')
            payment.state_transfer_queued()
    except DucatuscoreInterfaceError as e:
        payment.state_transfer_error()
        payment.save()
        raise TransferException(e)


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
    logger.info(msg=f'Created directory at: {p_dir}')

    if len(pl_eth) > 0:
        logger.info(msg='Write ETH payment stats')
        eth_file = os.path.join(p_dir, 'eth.csv')
        write_payments_to_csv(eth_file, pl_eth, DECIMALS['ETH'])
        logger.info(msg=f'Done, {len(pl_eth)} items saved to: {eth_file}')
    else:
        logger.info(msg='No payments in ETH at this period')

    if len(pl_btc) > 0:
        logger.info(msg='Write BTC payment stats')
        btc_file = os.path.join(p_dir, 'btc.csv')
        write_payments_to_csv(btc_file, pl_btc, DECIMALS['BTC'])
        logger.info(msg=f'Done, {len(pl_btc)} items saved to: {btc_file}')
    else:
        logger.info(msg='No payments in BTC at this period')

    if len(pl_usdc) > 0:
        logger.info(msg='Write USDC payment stats')
        usdc_file = os.path.join(p_dir, 'usdc.csv')
        write_payments_to_csv(usdc_file, pl_usdc, DECIMALS['USDC'])
        logger.info(msg=f'Done, {len(pl_usdc)} items saved to: {usdc_file}')
    else:
        logger.info(msg='No payments in USDC at this period')


def parse_payment_manually(tx_hash, currency):
    address_field_name = currency.lower() + '_address__iexact'
    if currency in ['DUC', 'BTC']:
        base_url = NETWORK_SETTINGS[currency].get('bitcore_url')
        if not base_url:
            raise ValueError(f'bitcore_url is not configured for {currency} network')

        url = '/'.join([base_url, 'tx', tx_hash, 'coins'])
        response = requests.get(url)

        if response.status_code == 404:
            raise ValueError(f'Transaction {tx_hash} not found')

        data = response.json()

        try:
            from_address = data['inputs'][0]['address']
        except (KeyError, IndexError):
            from_address = None

        for output in data['outputs']:
            try:
                exchange_request = ExchangeRequest.objects.get(**{ address_field_name: output['address'] })
            except ExchangeRequest.DoesNotExist:
                continue

            message = {
                    'exchangeId': exchange_request.pk,
                    'fromAddress': from_address,
                    'address': output['address'],
                    'transactionHash': tx_hash,
                    'currency': currency,
                    'amount': output['value'],
                    'success': True,
                    'status': 'COMMITED'
            }
            parse_payment_message(message)

    elif currency in ['USDT', 'USDC']:
        ETH_NETWORK = NETWORK_SETTINGS['ETH']

        w3 = Web3(HTTPProvider(ETH_NETWORK['url']))
        receipt = w3.eth.getTransactionReceipt(tx_hash)

        token = ETH_NETWORK['tokens'][currency]
        contract_address = token.get('address')
        if not contract_address:
            raise ValueError(f'address is not configured for {currency} network')

        with open(os.path.abspath(ERC20_ABI)) as f:
            abi = json.load(f)

        contract = w3.eth.contract(address=w3.toChecksumAddress(contract_address), abi=abi)
        receipt = contract.events.Transfer().processReceipt(receipt)
        if not receipt:
            logger.debug(f'{currency} transaction with tx_hash {tx_hash} returned empty contract receipt')
            return

        event = receipt[0].args
        try:
            exchange_request = ExchangeRequest.objects.get(eth_address__iexact=event.to)
        except ExchangeRequest.DoesNotExist:
            raise ValueError(f'Exchange request not found')

        message = {
            'exchangeId': exchange_request.id,
            'address': exchange_request.eth_address,
            'fromAddress': event['from'],
            'transactionHash': tx_hash,
            'currency': currency,
            'amount': event.value,
            'success': True,
            'status': 'COMMITED'
        }
        parse_payment_message(message)

    elif currency in ['DUCX', 'ETH']:
        w3 = Web3(HTTPProvider(NETWORK_SETTINGS[currency]['url']))
        receipt = w3.eth.getTransactionReceipt(tx_hash)
        tx = w3.eth.getTransaction(tx_hash)

        if receipt.status != 1:
            raise ValueError(f'Transaction {tx_hash} failed')

        try:
            exchange_request = ExchangeRequest.objects.get(**{ address_field_name: receipt.to })
        except ExchangeRequest.DoesNotExist:
            raise ValueError(f'Exchange request not found')

        message = {
            'exchangeId': exchange_request.pk,
            'fromAddress': tx['from'],
            'address': receipt['to'],
            'transactionHash': tx_hash,
            'currency': currency,
            'amount': tx.value,
            'success': True,
            'status': 'COMMITED'
        }
        parse_payment_message(message)
    else:
        raise ValueError(f'Invalid currency: {currency}')

def get_payments_status_from_hashes(payment_hashes_list: list):
    payment_data = []
    for p in payment_hashes_list:
        payment = Payment.objects.filter(tx_hash=p).first()     
        if not payment:
            status = 'Not received in scanner'
            payment_date = None
            return_tx = None
            transfer_tx = None
        else:
            payment_date = payment.created_date
            status = payment.transfer_state
            return_tx = payment.returned_tx_hash

            transfer = payment.transfers.first()
            if transfer and status == 'DONE':
                transfer_tx = transfer.tx_hash
            else:
                transfer_tx = None

        payment_data.append({
            'tx_hash': p,
            'status': status,
            'date': payment_date,
            'transfer_tx_hash': transfer_tx,
            'return_tx_hash': return_tx
        })  
        
    dt = timezone.now()
    with open(f'payments-{dt.year}-{dt.month}-{dt.day}.csv', 'w') as csvfile:
        fieldnames = ['tx_hash', 'status', 'date', 'transfer_tx_hash', 'return_tx_hash']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in payment_data:
            writer.writerow(row)

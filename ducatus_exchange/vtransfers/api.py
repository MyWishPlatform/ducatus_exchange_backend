import json
from decimal import Decimal

import requests
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, APIException

from ducatus_exchange.vouchers.models import Voucher
from ducatus_exchange.vtransfers.models import Transfer
from ducatus_exchange.litecoin_rpc import DucatuscoreInterface, DucatuscoreInterfaceException
from ducatus_exchange.consts import DECIMALS
from ducatus_exchange.settings import RATES_API_URL


def validate_voucher(activation_code):
    try:
        voucher = Voucher.objects.get(activation_code=activation_code)
    except ObjectDoesNotExist:
        raise PermissionDenied(detail='Invalid activation code')

    if not voucher.is_active:
        raise PermissionDenied(detail='This voucher is not active')

    if voucher.is_used:
        raise PermissionDenied(detail='This voucher already used')

    return voucher


def make_voucher_transfer(voucher, duc_address):
    duc_amount = convert_usd2duc(usd_amount=voucher.usd_amount)
    transfer = Transfer(voucher=voucher, duc_amount=duc_amount, duc_address=duc_address)
    transfer.save()

    try:
        rpc = DucatuscoreInterface()
        tx_hash = rpc.node_transfer(duc_address, duc_amount)
        transfer.tx_hash = tx_hash
        transfer.transfer_status = 'WAITING_FOR_CONFIRM'
        transfer.save()
        print(f'VOUCHER ACTIVATION: successful transfer {transfer.tx_hash} to {transfer.duc_address} '
              f'for {transfer.duc_amount} DUC', flush=True)
    except DucatuscoreInterfaceException as err:
        transfer.transfer_status = 'ERROR'
        transfer.save()
        print(f'VOUCHER ACTIVATION: failed transfer {transfer.duc_amount} DUC to {transfer.duc_address} '
              f'with exception {str(err)}', flush=True)
        raise APIException(detail=str(err))

    voucher.is_used = True
    voucher.activation_date = timezone.now()
    voucher.save()

    return transfer


def send_dividends(duc_address, duc_amount):
    transfer = Transfer(duc_amount=duc_amount, duc_address=duc_address)
    transfer.save()

    try:
        rpc = DucatuscoreInterface()
        tx_hash = rpc.node_transfer(duc_address, duc_amount)
    except DucatuscoreInterfaceException as err:
        transfer.transfer_status = 'ERROR'
        transfer.save()
        raise APIException(detail=str(err))

    transfer.tx_hash = tx_hash
    transfer.transfer_status = 'WAITING_FOR_CONFIRM'
    transfer.tag = 'dividends'
    transfer.save()

    return transfer


def confirm_voucher_transfer(message):
    tx_hash = message.get('txHash')
    transfer = Transfer.objects.get(tx_hash=tx_hash)
    transfer.transfer_status = 'CONFIRMED'
    transfer.save()

    if transfer.voucher.payment_id or transfer.voucher.charge_id:
        transfer.voucher.register_in_lottery(transfer)


def convert_usd2duc(usd_amount):
    duc_usd_rate = json.loads(requests.get(RATES_API_URL.format(fsym='DUC', tsyms='USD')).content).get('USD')
    duc_amount = Decimal(str(usd_amount / duc_usd_rate)) * DECIMALS['DUC']
    return duc_amount

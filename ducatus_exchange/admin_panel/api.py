import sys
import json
import time
import typing
import requests
import traceback
from decimal import Decimal

from bip32utils import BIP32Key
from eth_keys import keys
from eth_account import Account
from rest_framework.exceptions import NotFound
from bitcoinrpc.authproxy import JSONRPCException

from ducatus_exchange.bip32_ducatus import DucatusWallet
from ducatus_exchange.exchange_requests.models import ExchangeRequest
from ducatus_exchange.litecoin_rpc2 import DucatuscoreInterface
from ducatus_exchange.parity_interface2 import ParityInterface
from ducatus_exchange.payments.models import Payment
from ducatus_exchange.consts import CURRENCIES, DECIMALS
from ducatus_exchange.settings import ROOT_KEYS, COLLECTION_ADDRESSES, IS_TESTNET_PAYMENTS, NETWORK_SETTINGS


class LowBalance(Exception):
    pass


class InterfaceError(Exception):
    pass


def get_input_balance():
    res = {}
    for currency in CURRENCIES:
        amounts = Payment.objects.filter(collection_state='NOT_COLLECTED', currency=currency).values_list(
            'original_amount', flat=True)
        res[currency] = sum(amounts)

    return res


def get_output_balance():
    btc_interface = DucatuscoreInterface()
    duc_balance = btc_interface.rpc.getbalance('')

    eth_interface = ParityInterface('DUCX')
    ducx_balance = int(eth_interface.eth_getBalance(NETWORK_SETTINGS['DUCX']['address']), 16)

    res = {
        'DUC': duc_balance * DECIMALS['DUC'],
        'DUCX': ducx_balance,
    }

    return res


def withdraw_coins(currency):
    exchange_requests = ExchangeRequest.objects.all()
    for exchange_request in exchange_requests:
        payments = Payment.objects.filter(collection_state='NOT_COLLECTED',
                                          currency=currency,
                                          exchange_request=exchange_request)
        if payments:
            if currency in ['ETH', 'DUCX']:
                try:
                    collect_parity(payments, currency)
                    time.sleep(3)
                except (LowBalance, InterfaceError):
                    for payment in payments:
                        payment.collection_state = 'ERROR'
                        payment.save()
                    print('\n'.join(traceback.format_exception(*sys.exc_info())), flush=True)
            elif currency in ['DUC', 'BTC']:
                try:
                    collect_litecoin(payments, currency)
                except (LowBalance, InterfaceError, JSONRPCException):
                    for payment in payments:
                        payment.collection_state = 'ERROR'
                        payment.save()
                    print('\n'.join(traceback.format_exception(*sys.exc_info())), flush=True)
            else:
                raise NotFound


def collect_parity(payments: typing.List[Payment], currency: str):
    if currency == 'ETH':
        net_name = 'testnet' if IS_TESTNET_PAYMENTS else 'mainnet'
    elif currency == 'DUCX':
        net_name = 'ducatusx'
    else:
        print(f'currency {currency} not supported', flush=True)
        return

    x = BIP32Key.fromExtendedKey(ROOT_KEYS[net_name]['private'])

    exchange_request = payments[0].exchange_request
    child_private = keys.PrivateKey(x.ChildKey(exchange_request.user.id).k.to_string())
    amount = sum([payment.original_amount for payment in payments])
    from_address = exchange_request.eth_address if currency == 'ETH' else exchange_request.ducx_address

    interface = ParityInterface(currency)

    print(int(interface.eth_getBalance(from_address), 16), flush=True)
    print(amount, flush=True)
    print(from_address, flush=True)
    if int(interface.eth_getBalance(from_address), 16) < amount:
        raise LowBalance

    gas_price = int(interface.eth_gasPrice(), 16)
    gas = 21000

    tx = {
        'gasPrice': gas_price,
        'gas': gas,
        'to': COLLECTION_ADDRESSES[currency],
        'nonce': interface.eth_getTransactionCount(from_address, 'pending'),
        'value': int(amount - gas * gas_price),
    }
    print('tx_params', tx, flush=True)

    if tx['value'] <= 0:
        print('negative value', flush=True)
        return

    signed = Account.sign_transaction(tx, child_private)

    print('try collect {amount} {currency} from exchange {exchange_id}'.format(amount=tx['value'],
                                                                               currency=currency,
                                                                               exchange_id=exchange_request.id),
          flush=True)
    try:
        tx_hash = interface.eth_sendRawTransaction(signed.rawTransaction.hex())
        print('tx hash', tx_hash, flush=True)
    except Exception:
        raise InterfaceError

    for payment in payments:
        payment.collection_state = 'WAITING_FOR_CONFIRMATION'
        payment.collection_tx_hash = tx_hash
        payment.save()


def collect_litecoin(payments: typing.List[Payment], currency: str):
    exchange_request = payments[0].exchange_request
    # duc_root_key = DucatusWallet.deserialize(ROOT_KEYS['mainnet']['private'])
    # child_private = duc_root_key.get_child(exchange_request.user.id).export_to_wif().decode()

    x = BIP32Key.fromExtendedKey(ROOT_KEYS['mainnet']['private'])
    child_private = x.ChildKey(exchange_request.user.id).WalletImportFormat()


    from_address = exchange_request.btc_address
    print('from', from_address, flush=True)

    inputs_request = json.loads(requests.get(
        'https://api.bitcore.io/api/BTC/mainnet/address/{duc_address}'.format(
            duc_address=from_address)).content.decode())

    input_params = []
    for input_tx in inputs_request:
        if not input_tx['spentTxid']:
            input_params.append({
                'txid': input_tx['mintTxid'],
                'vout': input_tx['mintIndex'],
            })
    print('input_params', input_params, flush=True)

    interface = DucatuscoreInterface('BTC')

    amount = sum([payment.original_amount for payment in payments]) / DECIMALS['DUC'] - Decimal(0.00017040)
    if amount <= 0:
        print('negative value', flush=True)
        return

    output_params = {'3Lcg1u35tgBvSdWVe4WzvNhvcFN1YhqLQJ': amount}
    print('output_params', output_params, flush=True)

    tx = interface.rpc.createrawtransaction(input_params, output_params)
    print('raw tx', tx, flush=True)

    signed = interface.rpc.signrawtransaction(tx, None, [child_private])
    print('signed tx', signed, flush=True)

    tx_hash = interface.rpc.sendrawtransaction(signed['hex'])
    print('tx', tx_hash, flush=True)

    for payment in payments:
        payment.collection_state = 'WAITING_FOR_CONFIRMATION'
        payment.collection_tx_hash = tx_hash
        payment.save()

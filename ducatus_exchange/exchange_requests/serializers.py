import requests
import os
import hashlib
import binascii

from bip32utils import BIP32Key
from eth_keys import keys
from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from ducatus_exchange.settings import ROOT_KEYS, BITCOIN_URLS, IS_TESTNET_PAYMENTS
from ducatus_exchange.exchange_requests.models import ExchangeRequest, DucatusUser
from ducatus_exchange.bip32_ducatus import DucatusWallet


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


def init_exchange_request(duc_address):
    exchange_request = ExchangeRequest(duc_address)

    if IS_TESTNET_PAYMENTS:
        root_pub_key = ROOT_KEYS['testnet']['public']
    else:
        root_pub_key = ROOT_KEYS['mainnet']['public']

    request_key = BIP32Key.fromExtendedKey(root_pub_key, public=True)
    exchange_request.eth_address = request_key.ChildKey(exchange_request.id).Address()
    exchange_request.btc_address = keys.PublicKey(request_key.ChildKey(exchange_request.id).K.to_string()).to_checksum_address().lower()

    registration_btc_address(exchange_request.btc_address)
    return


def get_root_key():
    network = 'mainnet'

    if IS_TESTNET_PAYMENTS:
        network = 'testnet'

    root_pub_key = ROOT_KEYS[network]['public']

    return root_pub_key


class ExchangeRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeRequest
        fields = ['user', 'duc_address', 'ducx_address', 'eth_address', 'btc_address', 'to_currency']

    def create(self, validated_data):
        print('validated_data:', validated_data, flush=True)
        ducatus_user = validated_data['user']

        eth_btc_root_pub_key = get_root_key()
        eth_btc_root_key = BIP32Key.fromExtendedKey(eth_btc_root_pub_key, public=True)
        eth_btc_child_key = eth_btc_root_key.ChildKey(ducatus_user.id)
        btc_address = eth_btc_child_key.Address()
        registration_btc_address(btc_address)
        eth_address = keys.PublicKey(eth_btc_child_key.K.to_string()).to_checksum_address().lower()

        duc_root_key = DucatusWallet.deserialize(ROOT_KEYS['ducatus']['public'])
        duc_address = duc_root_key.get_child(ducatus_user.id, is_prime=False).to_address()

        ducx_root_pub__key = ROOT_KEYS['ducatusx']['public']
        ducx_root_key = BIP32Key.fromExtendedKey(ducx_root_pub__key, public=True)
        ducx_address = keys.PublicKey(ducx_root_key.K.to_string()).to_checksum_address().lower()

        validated_data['user_id'] = ducatus_user.id
        validated_data['btc_address'] = btc_address
        validated_data['eth_address'] = eth_address
        validated_data['duc_address'] = duc_address
        validated_data['ducx_address'] = ducx_address

        return super().create(validated_data)

    def is_valid(self, raise_exception=False):
        if hasattr(self, 'initial_data'):
            try:
                obj = ExchangeRequest.objects.get(**self.initial_data)
            except (ObjectDoesNotExist, MultipleObjectsReturned):
                return super().is_valid(raise_exception)
            else:
                self.instance = obj
                return super().is_valid(raise_exception)
        else:
            return super().is_valid(raise_exception)

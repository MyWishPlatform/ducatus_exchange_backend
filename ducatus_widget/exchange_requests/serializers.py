import requests
import os
import hashlib
import binascii

from bip32utils import BIP32Key
from eth_keys import keys
from rest_framework import serializers

from ducatus_widget.settings import ROOT_PUBLIC_KEY, BITCOIN_URLS
from ducatus_widget.exchange_requests.models import ExchangeRequest, DucatusAddress


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

    request_key = BIP32Key.fromExtendedKey(ROOT_PUBLIC_KEY, public=True)
    exchange_request.eth_address = request_key.ChildKey(exchange_request.id).Address()
    exchange_request.btc_address = keys.PublicKey(request_key.ChildKey(exchange_request.id).K.to_string()).to_checksum_address().lower()

    # registration_btc_address(exchange_request.btc_address)
    return


class ExchangeRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeRequest
        fields = ['duc_address', 'eth_address', 'btc_address']

    def create(self, validated_data):
        duc_addr = DucatusAddress(address=validated_data['duc_address'])
        duc_addr.save()

        root_key = BIP32Key.fromExtendedKey(ROOT_PUBLIC_KEY, public=True)
        child_key = root_key.ChildKey(duc_addr.id)

        validated_data['user_id'] = duc_addr.id
        validated_data['btc_address'] = child_key.Address()
        validated_data['eth_address'] = keys.PublicKey(child_key.K.to_string()).to_checksum_address().lower()

        print(validated_data)

        return super().create(validated_data)

import binascii
import os

import requests

from ducatus_exchange.settings import ROOT_KEYS, BITCOIN_URL, IS_TESTNET_PAYMENTS


def generate_memo(m):
    memo_str = os.urandom(8)
    m.update(memo_str)
    memo_str = binascii.hexlify(memo_str + m.digest()[0:2])
    return memo_str


def registration_btc_address(btc_address):
    requests.post(
        BITCOIN_URL,
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

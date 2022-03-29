import json
import requests
import logging

from eth_utils import to_checksum_address
from eth_account import Account
from web3 import Web3

from ducatus_exchange.settings import NETWORK_SETTINGS, DUCX_GAS_PRICE, DUCX_TRANSFER_GAS_LIMIT
from ducatus_exchange.consts import DECIMALS

logger = logging.getLogger('parity_interface')


class ParityInterfaceException(Exception):
    pass


class ParConnectExc(Exception):
    def __init__(self, *args):
        self.value = 'can not connect to parity'

    def __str__(self):
        return self.value


class ParErrorExc(Exception):
    pass

    
class ParityInterface:

    endpoint = None
    settings = None

    def __init__(self):

        self.settings = NETWORK_SETTINGS['DUCX']
        self.setup_endpoint()
        # self.check_connection()

    def setup_endpoint(self):
        self.endpoint = '{schema}://{host}:{port}'.format(
            host=self.settings['host'],
            port=self.settings['port'],
            schema=self.settings['schema']
        )
        self.settings['chainId'] = self.eth_chainId()
        logger.info(msg=f'parity interface {self.settings}')
        return

    def __getattr__(self, method):
        def f(*args):
            arguments = { 
                    'method': method,
                    'params': args,
                    'id': 1,
                    'jsonrpc': '2.0',
            }
            try:
                temp = requests.post(
                    self.endpoint,
                    json=arguments,
                    headers={'Content-Type': 'application/json'}
                )
            except requests.exceptions.ConnectionError as e:
                raise ParConnectExc()
            result = json.loads(temp.content.decode())
            if result.get('error'):
                raise ParErrorExc(result['error']['message'])
            return result['result']
        return f

    def transfer(self, address, amount, from_address=None, from_private=None):
        if not from_address:
            from_address = self.settings['address']
        if not from_private:
            from_private = self.settings['private']

        logger.info(msg='DUCATUSX TRANSFER STARTED: {address}, {amount} DUCX'.format(
            address=address,
            amount=amount / DECIMALS['DUCX']
        ))

        nonce = self.eth_getTransactionCount(from_address, "pending")
        gas_price = self.eth_gasPrice()
        chain_id = self.settings['chainId']

        tx_params = {
            'to': to_checksum_address(address),
            'value': int(amount),
            'gas': DUCX_TRANSFER_GAS_LIMIT,
            'gasPrice': DUCX_GAS_PRICE,
            'nonce': int(nonce, 16),
            'chainId': int(chain_id, 16)
        }
        logger.info(msg=f'TX PARAMS {tx_params}')

        signed = Account.sign_transaction(tx_params, from_private)

        try:
            sent = self.eth_sendRawTransaction(signed.rawTransaction.hex())
            logger.info(msg=f'TXID: {sent}')
            return sent
        except Exception as e:
            err = 'DUCATUSX TRANSFER ERROR: transfer for {amount} DUCX for {addr} failed' \
                .format(amount=amount / DECIMALS['DUCX'], addr=address)
            logger.error(msg=err)
            logger.error(msg=e)
            raise ParityInterfaceException(err)

    def get_balance(self):
        address = NETWORK_SETTINGS['DUCX']['address']
        raw_balance = self.eth_getBalance(Web3.toChecksumAddress(address))
        balance = int(raw_balance, 16)
        return balance

    def get_transaction(self, tx_hash):
        return int(self.eth_getTransactionByHash(tx_hash).get('blockNumber'), 16)

    def get_block_count(self):
        return int(self.eth_getBlockByNumber('latest', True).get('number'), 16)

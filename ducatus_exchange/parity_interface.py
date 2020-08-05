import json
import requests
from eth_utils import to_checksum_address
from eth_account import Account

from ducatus_exchange.settings import NETWORK_SETTINGS
from ducatus_exchange.consts import DECIMALS


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

    def __init__(self, network):

        self.settings = NETWORK_SETTINGS[network]
        self.setup_endpoint()
        # self.check_connection()

    def setup_endpoint(self):
        # self.endpoint = 'http://{host}:{port}'.format(
        #     host=self.settings['host'],
        #     port=self.settings['port']
        # )
        self.endpoint = self.settings['url']
        self.settings['chainId'] = self.eth_chainId()
        print('parity interface', self.settings, flush=True)
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

    def transfer(self, address, amount):
        print('DUCATUSX TRANSFER STARTED: {address}, {amount} DUCX'.format(
            address=address,
            amount=amount / DECIMALS['DUCX']
        ), flush=True)

        nonce = self.eth_getTransactionCount(self.settings['address'], "pending")
        gas_price = self.eth_gasPrice()
        chain_id = self.settings['chainId']

        tx_params = {
            'to': to_checksum_address(address),
            'value': int(amount),
            'gas': 30000,
            'gasPrice': int(gas_price, 16) * 2,
            'nonce': int(nonce, 16),
            'chainId': int(chain_id, 16)
        }
        print('TX PARAMS', tx_params, flush=True)

        signed = Account.sign_transaction(tx_params, self.settings['private'])

        try:
            sent = self.eth_sendRawTransaction(signed.rawTransaction.hex())
            print('TXID:', sent, flush=True)
            return sent
        except Exception as e:
            err = 'DUCATUSX TRANSFER ERROR: transfer for {amount} DUCX for {addr} failed' \
                .format(amount=amount / DECIMALS['DUCX'], addr=address)
            print(err, flush=True)
            print(e, flush=True)
            raise ParityInterfaceException(err)



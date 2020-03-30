import json
import requests
from web3 import Web3, HTTPProvider

from ducatus_exchange.settings import NETWORK_SETTINGS


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
        self.endpoint = 'http://{host}:{port}'.format(
            host=self.settings['host'],
            port=self.settings['port']
        )
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
        nonce = int(self.eth_getTransactionCount(self.settings['address'], "pending"), 16)
        print('nonce', nonce, flush=True)

        tx_params = {
            'to': address,
            'value': int(amount),
            'gas': 21000,
            'gasPrice': 2 * 10 ** 9,
            'nonce': nonce + 1,
            'chainId': self.settings['chainId']
        }

        w3 = Web3(HTTPProvider(self.endpoint))

        signed_tx = w3.eth.account.signTransaction(tx_params, self.settings['private'])

        try:
            tx = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
            print(tx.hex())
            return tx.hex()
        except Exception as e:
            err = 'DUCATUSX TRANSFER ERROR: transfer for {amount} DUC for {addr} failed' \
                .format(amount=amount, addr=address)
            print(err, flush=True)
            print(e, flush=True)
            raise ParityInterfaceException(err)













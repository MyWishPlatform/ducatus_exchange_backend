import json
import requests
import web3

from ducatus_exchange.settings import NETWORK_SETTINGS



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
        print('parity interface', self.addr, self.port, flush=True)
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

        tx_params = {
            'to': address,
            'value': amount,
            'gas': 21000,
            'gasPrice': 2 * 10 ** 9,
            'nonce': nonce,
            'chainId': self.settings['chainId']
        }

        signed_tx = web3.eth.account.signTransaction(tx_params, self.settings['private'])

        try:
            tx = self.eth_sendRawTransaction(signed_tx)
            print(tx)
            return tx
        except (ParConnectExc, ParErrorExc) as e:
            print('DUCATUSX TRANSFER ERROR: transfer for {amount} DUC for {addr} failed'
                  .format(amount=amount, addr=address), flush=True
                  )
            print(e, flush=True)











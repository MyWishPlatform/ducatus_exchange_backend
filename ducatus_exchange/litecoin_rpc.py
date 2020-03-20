from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

from ducatus_exchange.settings import NETWORK_SETTINGS
from ducatus_exchange.consts import DECIMALS


class DucatuscoreInterfaceException(Exception):
    pass


class DucatuscoreInterface:

    endpoint = None
    settings = None

    def __init__(self):

        self.settings = NETWORK_SETTINGS['DUC']
        self.setup_endpoint()
        self.rpc = AuthServiceProxy(self.endpoint)
        self.check_connection()

    def setup_endpoint(self):
        self.endpoint = 'http://{user}:{pwd}@{host}:{port}'.format(
            user=self.settings['user'],
            pwd=self.settings['password'],
            host=self.settings['host'],
            port=self.settings['port']
        )
        return

    def check_connection(self):
        block = self.rpc.getblockcount()
        if block and block > 0:
            return True
        else:
            raise Exception('Ducatus node not connected')

    def transfer(self, address, amount):
        try:
            value = amount / DECIMALS['DUC']
            print('try sending {value} DUC to {addr}'.format(value=value, addr=address))
            self.rpc.walletpassphrase(self.settings['wallet_password'], 30)
            res = self.rpc.sendtoaddress(address, value)
            print(res)
            return res
        except JSONRPCException as e:
            err = 'DUCATUS TRANSFER ERROR: transfer for {amount} DUC for {addr} failed'\
                .format(amount=amount, addr=address)
            print(err, flush=True)
            print(e, flush=True)
            raise DucatuscoreInterfaceException(err)



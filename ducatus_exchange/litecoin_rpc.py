from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

from ducatus_exchange.settings import NETWORK_SETTINGS


class DucatuscoreInterface:

    endpoint = None
    settings = None

    def __init__(self):

        self.setup_endpoint()
        self.rpc = AuthServiceProxy(self.endpoint)
        self.check_connection()

    def setup_endpoint(self):
        settings = NETWORK_SETTINGS['DUC']
        #duc_settings = NETWORK_SETTINGS['LTC']

        self.endpoint = 'http://{user}:{pwd}@{host}:{port}'.format(
            user=settings['user'],
            pwd=settings['password'],
            host=settings['host'],
            port=settings['port']
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
            self.rpc.walletpassphrase(self.settings['wallet_password'], 30)
            res = self.rpc.sendtoaddress(address, amount)
            print(res)
            return res
        except JSONRPCException as e:
            print('DUCATUS TRANSFER ERROR: transfer for {amount} DUC for {addr} failed'
                  .format(amount=amount, addr=address), flush=True
                  )
            print(e, flush=True)



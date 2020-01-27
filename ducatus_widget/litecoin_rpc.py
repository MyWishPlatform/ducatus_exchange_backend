from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

from ducatus_widget.settings import NETWORK_SETTINGS


class DucatuscoreInterface:

    endpoint = None

    def __init__(self):

        self.setup_endpoint()
        self.rpc = AuthServiceProxy(self.endpoint)
        self.check_connection()

    def setup_endpoint(self):
        duc_settings = NETWORK_SETTINGS['DUC']

        self.endpoint = 'http://{user}:{pwd}@{host}:{port}'.format(
            user=duc_settings['user'],
            pwd=duc_settings['password'],
            host=duc_settings['host'],
            port=duc_settings['port']
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
            res = self.rpc.sendtoaddress(address, amount)
            print(res)
            return res
        except Exception as e:
            print('DUCATUS TRANSFER ERROR: transfer for {amount} DUC for {addr} failed'
                  .format(amount=amount, addr=address), flush=True
                  )
            print(e, flush=True)



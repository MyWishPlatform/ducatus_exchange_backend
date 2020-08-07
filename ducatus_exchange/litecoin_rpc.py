from decimal import Decimal
from http.client import RemoteDisconnected

from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

from ducatus_exchange.settings import NETWORK_SETTINGS
from ducatus_exchange.consts import DECIMALS


class DucatuscoreInterfaceException(Exception):
    pass


class DucatuscoreInterface:
    endpoint = None
    settings = None

    def __init__(self, network):

        self.settings = NETWORK_SETTINGS[network]
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
            err = 'DUCATUS TRANSFER ERROR: transfer for {amount} DUC for {addr} failed' \
                .format(amount=amount, addr=address)
            print(err, flush=True)
            print(e, flush=True)
            raise DucatuscoreInterfaceException(err)

    def validate_address(self, address):
        for attempt in range(10):
            print('attempt', attempt, flush=True)
            try:
                rpc_response = self.rpc.validateaddress(address)
            except RemoteDisconnected as e:
                print(e, flush=True)
                rpc_response = False
            if not isinstance(rpc_response, bool):
                print(rpc_response, flush=True)
                break
        else:
            raise Exception(
                'cannot validate address with 10 attempts')

        return rpc_response['isvalid']

    def get_unspent(self, tx_hash, count):
        return self.rpc.gettxout(tx_hash, count)

    def get_fee(self):
        return self.rpc.getinfo()['relayfee']

    def get_unspent_input(self, tx_hash, payment_address):
        last_response = {}
        count = 0
        while isinstance(last_response, dict):
            rpc_response = self.get_unspent(tx_hash, count)
            last_response = rpc_response

            input_addresses = rpc_response['scriptPubKey']['addresses']
            if payment_address in input_addresses:
                return rpc_response, count

            count += 1

    def internal_transfer(self, tx_list, address_from, address_to, amount, private_key):
        print('start raw tx build', flush=True)
        print('tx_list', tx_list, 'from', address_from, 'to', address_to, 'amount', amount, flush=True)
        try:
            input_params = []
            for payment_hash in tx_list:
                unspent_input, input_vout_count = self.get_unspent_input(payment_hash, address_from)
                print('unspent input', unspent_input, flush=True)

                input_params.append({
                    'txid': payment_hash,
                    'vout': input_vout_count
                })

            transaction_fee = self.get_fee() * DECIMALS['DUC']
            send_amount = (Decimal(amount) - transaction_fee) / DECIMALS['DUC']

            print('input_params', input_params, flush=True)
            output_params = {address_to: send_amount}
            print('output_params', output_params, flush=True)

            tx = self.rpc.createrawtransaction(input_params, output_params)
            print('raw tx', tx, flush=True)

            signed = self.rpc.signrawtransaction(tx, None, [private_key])
            print('signed tx', signed, flush=True)

            tx_hash = self.rpc.sendrawtransaction(signed['hex'])
            print('tx', tx_hash, flush=True)

            return tx_hash

        except JSONRPCException as e:
            print('DUCATUS TRANSFER ERROR: transfer for {amount} DUC for {addr} failed'
                  .format(amount=amount, addr=address_to), flush=True
                  )
            print(e, flush=True)
            raise DucatuscoreInterfaceException(e)

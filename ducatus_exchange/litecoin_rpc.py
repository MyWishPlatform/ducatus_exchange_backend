import logging

from decimal import Decimal
from http.client import RemoteDisconnected

from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

from ducatus_exchange.settings import NETWORK_SETTINGS
from ducatus_exchange.consts import DECIMALS


logger = logging.getLogger('litecoin_rpc')


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
            logger.info(msg=f'try sending {value} DUC to {address}')
            self.rpc.walletpassphrase(self.settings['wallet_password'], 30)
            res = self.rpc.sendtoaddress(address, value)
            logger.info(msg=res)
            return res
        except JSONRPCException as e:
            err = f'DUCATUS TRANSFER ERROR: transfer for {amount} DUC for {address} failed'
            logger.error(msg=err)
            logger.error(msg=e)
            raise DucatuscoreInterfaceException(err)

    def validate_address(self, address):
        for attempt in range(10):
            logger.info(msg=f'attempt {attempt}')
            try:
                rpc_response = self.rpc.validateaddress(address)
            except RemoteDisconnected as e:
                logger.error(msg=e)
                rpc_response = False
            if not isinstance(rpc_response, bool):
                logger.info(msg=rpc_response)
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
        logger.info(msg='start raw tx build')
        logger.info(msg=f'tx_list {tx_list} from {address_from} to {address_to} amount {amount}')
        try:
            input_params = []
            for payment_hash in tx_list:
                unspent_input, input_vout_count = self.get_unspent_input(payment_hash, address_from)
                logger.info(msg=f'unspent input {unspent_input}')

                input_params.append({
                    'txid': payment_hash,
                    'vout': input_vout_count
                })

            transaction_fee = self.get_fee() * DECIMALS['DUC']
            send_amount = (Decimal(amount) - transaction_fee) / DECIMALS['DUC']

            logger.info(msg=f'input_params {input_params}')
            output_params = {address_to: send_amount}
            logger.info(msg=f'output_params {output_params}')

            tx = self.rpc.createrawtransaction(input_params, output_params)
            logger.info(msg=f'raw tx {tx}')

            signed = self.rpc.signrawtransaction(tx, None, [private_key])
            logger.info(msg=f'signed tx {signed}')

            tx_hash = self.rpc.sendrawtransaction(signed['hex'])
            logger.info(msg=f'tx {tx_hash}')

            return tx_hash

        except JSONRPCException as e:
            logger.error(msg=f'DUCATUS TRANSFER ERROR: transfer for {amount} DUC for {address_to} failed')
            logger.error(msg=e)
            raise DucatuscoreInterfaceException(e)

    def get_balance(self):
        # return self.rpc.getbalance('')
        return self.rpc.getbalance('') * DECIMALS['DUC']

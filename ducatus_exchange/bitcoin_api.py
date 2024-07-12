import json
import time
import requests
import httpx
import asyncio
import logging
from typing import Optional
from decimal import Decimal
from dataclasses import dataclass
from bitcoinrpc import BitcoinRPC as AsyncBitcoinRPC
from http.client import RemoteDisconnected, CannotSendRequest
from socket import timeout

from ducatus_exchange.settings import NETWORK_SETTINGS
from ducatus_exchange.consts import DECIMALS

logger = logging.getLogger(__name__)

class DucatuscoreInterfaceError(Exception):
    pass


def retry_on_http_disconnection(req):
    def wrapper(*args, **kwargs):
        for attempt in range(10):
            logger.info(f"attempt:{attempt}")
            try:
                return req(*args, **kwargs)
            except RemoteDisconnected as e:
                logger.warning(e)
                rpc_response = False
            except (timeout, TimeoutError, CannotSendRequest) as e:
                logger.warning(e)
                rpc_response = False
            if not isinstance(rpc_response, bool):
                logger.debug(rpc_response)
                break
        else:
            raise DucatuscoreInterfaceError("cannot execute request with 10 attempts")

    return wrapper



@dataclass
class BitcoinSettings:
    host: str
    port: int
    user: str
    password: str
    decimals: int
    wallet_password: Optional[str]

class DucatuscoreInterface:
    def __init__(self, settings, decimals, is_bitcoin):
        self.settings = BitcoinSettings(
            user=settings['user'],
            password=settings['password'],
            host=settings['host'],
            port=settings['port'],
            decimals=decimals,
            wallet_password=settings['wallet_password'] if 'wallet_password' in settings else None
        )
        self.endpoint = None
        self.setup_endpoint()   
        timeout = httpx.Timeout(
            60,
            connect=30.0,  # Connection timeout in seconds
            read=60.0,    # Read timeout in seconds
            write=60.0   # Write timeout in seconds
        )
        self.rpc = AsyncBitcoinRPC.from_config(*self.endpoint, timeout=timeout)
        self.decimals = self.settings.decimals
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.check_connection()
        self.set_params(is_bitcoin)

    def set_params(self, is_bitcoin):
        self.network_info = None
        self.version = None
        self.relay_fee = None

        if is_bitcoin:
            self.network_info = self.call_async("getnetworkinfo")
            self.version = int(str(self.network_info['version'])[:2])
            res = requests.get('https://api.bitcore.io/api/BTC/mainnet/fee/3')
            self.relay_fee = int(json.loads(res.text)['feerate'] * DECIMALS['BTC'])

    def setup_endpoint(self) -> None:
        self.endpoint = (
            f"http://{self.settings.host}:{self.settings.port}",
            (self.settings.user, self.settings.password)
        )

    @retry_on_http_disconnection
    def call_async(self, method_name, *args, **kwargs) -> object:
        async_method = getattr(self.rpc, method_name)
        result = self.loop.run_until_complete(async_method(*args, **kwargs))
        return result
    

    def construct_and_send_tx(self, input_params, output_params, private_key):
        try:
            raw_tx = self.call_async("acall", "createrawtransaction", (input_params, output_params))
            logger.info(msg=f'raw tx {raw_tx}')
            signed_tx = self.call_async("acall", "signrawtransaction", (raw_tx, None, [private_key]))
            logger.info(msg=f'signed tx {signed_tx}')
            tx_hash = self.call_async("acall", "sendrawtransaction", (signed_tx["hex"]))
            logger.info(msg=f"RAW TX HASH: {tx_hash}")
            return tx_hash

        except Exception as e:
            err = f"DUCATUS TRANSFER ERROR: {e}"
            logger.error(err)
            return None

    def validateaddress(self, address):
        return self.call_async("acall", "validateaddress", [address])
    
    def check_connection(self) -> bool:
        block = self.call_async("getblockcount")
        if not block and block > 0:
            raise DucatuscoreInterfaceError("Ducatus node not connected")

        return True
    
    def get_wallet_balance(self) -> float:
        response = self.call_async("acall", "getbalance", [])
        if type(response) in [float, int]:
            return response * self.decimals
        else:
            logger.warning(f"Could not fetch valid response on method 'getbalance', response is: {response}")
            return 0.0
    
    def transfer(self, to_address: str, amount: int) -> str:
        amount = Decimal(str(amount))
        """Mostly used for sending DUC from Master to User wallet"""
        if not (Decimal(self.get_wallet_balance()) - amount) > 0:
            raise ValueError
        try:
            amount_no_decimals = amount / Decimal(self.decimals)
            self.call_async("acall", "walletpassphrase", (self.settings.wallet_password, 30))
            tx_hash = self.call_async("acall", "sendtoaddress", (to_address, float(amount_no_decimals)))
            logger.info(msg=f"NODE TRANSFER HASH: {tx_hash}")
            return tx_hash

        except Exception as e:
            err = f"DUCATUS TRANSFER ERROR: {e}"
            logger.error(err)
            raise DucatuscoreInterfaceError(err)
    
    def validate_address(self, address):
        for attempt in range(10):
            logger.info(msg=f'attempt {attempt}')
            try:
                rpc_response = self.validateaddress(address)
            except Exception as e:
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
        return self.call_async("acall", "gettxout", [tx_hash, count])

    def get_fee(self):
        return self.call_async("acall", "getinfo")['relayfee']
    
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

            transaction_fee = Decimal(str(self.get_fee())) * Decimal(self.settings.decimals)
            send_amount = (Decimal(amount) - transaction_fee) / Decimal(self.settings.decimals)

            logger.info(msg=f'input_params {input_params}')
            output_params = {address_to: send_amount}
            logger.info(msg=f'output_params {output_params}')

            tx = self.call_async("acall", "createrawtransaction", (input_params, output_params))
            logger.info(msg=f'raw tx {tx}')

            signed = self.call_async("acall", "signrawtransaction", (tx, None, [private_key]))
            logger.info(msg=f'signed tx {signed}')

            tx_hash = self.call_async("acall", "sendrawtransaction", (signed["hex"]))
            logger.info(msg=f'tx {tx_hash}')

            return tx_hash

        except Exception as e:
            logger.error(msg=f'DUCATUS TRANSFER ERROR: transfer for {amount} DUC for {address_to} failed')
            logger.error(msg=e)
            raise DucatuscoreInterfaceError(e)
        

    def get_balance(self):
        balance = self.call_async("acall", "getbalance", [""])
        return int(balance * self.settings.decimals)

    def get_transaction(self, tx_hash):
        return self.call_async("acall", "getrawtransaction", [tx_hash, 1])
    
    def send_many(self, transfers):
        try:
            self.call_async("acall", "walletpassphrase", (self.settings.wallet_password, 30))
            transfer_hash = self.call_async("acall", "sendmany", ["", transfers])
            logger.info(transfer_hash)
        except Exception as e:
            logger.error(e)
            transfer_hash = "transfer_error"
        return transfer_hash
    
    def get_account_address(self):
        return self.call_async("acall", "getaccountaddress", [""])
    

class BitcoinAPI:
    def __init__(self):
        self.network = 'testnet'
        if 'production' in NETWORK_SETTINGS['BTC']:
            if NETWORK_SETTINGS['BTC']['production']:
                self.network = 'mainnet'

        self.base_url = None
        self.set_base_url()

    def set_base_url(self):
        self.base_url = f'https://api.bitcore.io/api/BTC/{self.network}'

    def get_address_response(self, address):
        endpoint_url = f'{self.base_url}/address/{address}/?limit=1000'
        res = requests.get(endpoint_url)
        if not res.ok:
            return [], False
        else:
            valid_json = len(res.json()) > 0
            if not valid_json:
                print('Address have no transactions and balance is 0', flush=True)
                return [], True

            return res.json(), True

    def get_address_unspent_all(self, address):
        inputs_of_address, response_ok = self.get_address_response(address)
        if not response_ok:
            return [], 0, False

        if response_ok and len(inputs_of_address) == 0:
            return inputs_of_address, 0, True

        inputs_value = 0
        unspent_inputs = []
        for input_tx in inputs_of_address:
            if not input_tx['spentTxid'] and input_tx['mintHeight'] > 1:
                unspent_inputs.append({
                    'txid': input_tx['mintTxid'],
                    'vout': input_tx['mintIndex']
                })
                inputs_value += input_tx['value']

        return unspent_inputs, inputs_value, True

    def get_address_unspent_from_tx(self, address, tx_hash):
        inputs_of_address, response_ok = self.get_address_response(address)
        if not response_ok:
            return [], 0, False

        if response_ok and len(inputs_of_address) == 0:
            return inputs_of_address, 0, True

        # find vout
        vout = None
        input_value = 0
        for input_tx in inputs_of_address:
            if not input_tx['spentTxid'] and input_tx['mintTxid'] == tx_hash:
                vout = input_tx['mintIndex']
                input_value = input_tx['value']

        if vout is None:
            return [], 0, False

        input_params = [{'txid': tx_hash, 'vout': vout}]
        return input_params, input_value, True

    def get_return_address(self, tx_hash):
        endpoint_url = f'{self.base_url}/tx/{tx_hash}/coins'
        res = requests.get(endpoint_url)
        if not res.ok:
            return '', False
        else:
            tx_info = res.json()

        inputs_of_tx = tx_info['inputs']
        if len(inputs_of_tx) == 0:
            return '', False

        first_input = inputs_of_tx[0]
        return_address = first_input['address']

        address_found = False
        if return_address:
            address_found = True

        return return_address, address_found

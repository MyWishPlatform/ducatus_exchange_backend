from urllib import parse
#from jsonrpcclient.clients.http_client import HTTPClient
from web3 import Web3, WebsocketProvider
from eth_typing import URI
from ethtoken.abi import EIP20_ABI
from ducatus_widget.settings import BACKEND_WALLETS


class ParityInterface:

    def __init__(self):
        eth_wallet = BACKEND_WALLETS['ETH']

        self.provider = WebsocketProvider(URI('ws://{}:{}'.format(eth_wallet['url'], eth_wallet['port'])))
        self.parity_node = Web3(self.provider)

        self.address = eth_wallet['address']
        print('connected: ', self.parity_node.isConnected(), flush=True)

    def transfer(self, amount):
        pass
        # web3.eth.contract(address, abi=standard_token_abi).sendTransaction({
        #     'from': from_address
        # }).transfer(to_address, amount)

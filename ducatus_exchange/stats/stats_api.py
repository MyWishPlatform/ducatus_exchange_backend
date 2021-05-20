import datetime

import requests
import logging


logging.basicConfig(level=logging.INFO)

#CURRENT_BLOCK_TIME = "2021-03-03T12:14:54.000Z"
#LOOKUP_TIME = "2021-02-21T00:00:00.000Z"
TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"


class DucatusAPI:

    def __init__(self):
        self.network = 'mainnet'
        self.base_url = None
        self.set_base_url()

    def set_base_url(self):
        self.base_url = f'https://ducapi.rocknblock.io/api/DUC/{self.network}'

    def get_address_response(self, address):
        endpoint_url = f'{self.base_url}/address/{address}'
        res = requests.get(endpoint_url)
        if not res.ok:
            return [], False
        else:
            valid_json = len(res.json()) > 0
            if not valid_json:
                print('Address have no transactions and balance is 0', flush=True)
                return [], True
            return res.json(), True

    def get_return_address(self, tx_hash):
        endpoint_url = f'{self.base_url}/tx/{tx_hash}/coins'
        res = requests.get(endpoint_url)
        if not res.ok:
            return '', False, res
        else:
            tx_info = res.json()

        inputs_of_tx = tx_info['inputs']
        if len(inputs_of_tx) == 0:
            return '', False, res

        first_input = inputs_of_tx[0]
        return_address = first_input['address']

        address_found = False
        if return_address:
            address_found = True

        return return_address, address_found, res

    def get_last_blockchain_block(self):
        req_string = f'{self.base_url}/block/'
        res = requests.get(req_string)
        data = res.json()
        blockchain_last_block = data[0]["height"]
        return blockchain_last_block

    def get_block_transactions(self, block_number):
        req_string = f'{self.base_url}/tx?blockHeight=' + str(block_number)
        logging.info(req_string)
        res = requests.get(req_string)
        data = res.json()

        sending_transactions = []
        for tx in data:
            if tx.get('value') not in (0, -1):
                sending_transactions.append(tx)

        return sending_transactions

    def get_transactions_from_blocks(self, now_block, scan_until_block):
        txs = []
        current_block = now_block

        while current_block <= scan_until_block:
            txs_in_block = self.get_block_transactions(current_block)
            if len(txs_in_block) > 0:
                for transaction in txs_in_block:
                    txs.append(transaction)

            logging.info('{block}, {tx_count}'.format(block=current_block, tx_count=len(txs)))
            current_block += 1

        return txs

    def get_tx_value(self, tx):
        tx_id = tx.get('txid')
        return_address, found, tx_request = self.get_return_address(tx_id)
    
        if found:
            value = 0
            for output in tx_request.json().get('outputs'):
                if output.get('address') != return_address:
                    value += int(output.get('value'))
        else:
            value = tx.get('value')
    
        return value

    def get_last_block_time(self, block):
        req_string = f'{self.base_url}/block/{block}'
        res = requests.get(req_string)
        data = res.json()
        time = data.get('time')
        time_date = datetime.datetime.strptime(time, '%Y-%m-%dT%H:%M:%S.%fZ')
        return time_date


class DucatusXAPI(DucatusAPI):
    def set_base_url(self):
        self.base_url = f'https://ducapi.rocknblock.io/api/DUCX/{self.network}'
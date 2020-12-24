import requests
from decimal import Decimal

from ducatus_exchange.transfers.models import DucatusTransfer
from ducatus_exchange.payments.models import Payment
from ducatus_exchange.consts import DECIMALS
from ducatus_exchange.litecoin_rpc import DucatuscoreInterface
from ducatus_exchange.bip32_ducatus import DucatusWallet
from ducatus_exchange.settings import ROOT_KEYS

class DucatusAPI:
    def __init__(self):
        self.set_base_url()

    def set_base_url(self):
        self.base_url = f'https://ducapi.rocknblock.io/api/DUC/mainnet'

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

    def get_address_unspent_all(self, address):
        inputs_of_address, response_ok = self.get_address_response(address)
        if not response_ok:
            return [], 0, False

        if response_ok and len(inputs_of_address) == 0:
            return inputs_of_address, 0, True

        inputs_value = 0
        unspent_inputs = []
        for input_tx in inputs_of_address:
            if not input_tx['spentTxid']:
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


def return_ducatus(payment_hash, amount):
    p = Payment.objects.get(tx_hash=payment_hash)

    duc_root_key = DucatusWallet.deserialize(ROOT_KEYS['ducatus']['private'])
    duc_child = duc_root_key.get_child(p.exchange_request.user.id, is_prime=False)
    child_private = duc_child.export_to_wif().decode()

    # if p.transfer_state in ['ERROR', 'WAITING_FOR_TRANSFER']:
    #     amount = p.original_amount
    # elif p.transfer_state == 'DONE':
    #     orig_duc_amount = p.original_amount
    #
    #     dt = DucatusTransfer.objects.get(payment=p)
    #     sent_ducx_amount = dt.amount
    #
    #     if (sent_ducx_amount / DECIMALS['DUCX']) < (orig_duc_amount / DECIMALS['DUC'] / 10):
    #         amount =
    # else:
    #     print('state not defined:', p.transfer_state, flush=True)
    #     return

    duc_api = DucatusAPI()
    duc_rpc = DucatuscoreInterface()

    fee = duc_rpc.get_fee() * DECIMALS['DUC']
    send_amount = (Decimal(amount) - fee) / DECIMALS['DUC']

    input_params = duc_api.get_address_unspent_from_tx(p.exchange_request.duc_address, p.tx_hash)
    print('input_params', input_params, flush=True)

    return_address = duc_api.get_return_address(p.tx_hash)

    output_params = {return_address: send_amount}
    print('output_params', output_params, flush=True)

    tx = duc_rpc.rpc.createrawtransaction(input_params, output_params)
    print('raw tx', tx, flush=True)

    signed = duc_rpc.rpc.signrawtransaction(tx, None, [child_private])
    print('signed tx', signed, flush=True)

    tx_hash = duc_rpc.rpc.sendrawtransaction(signed['hex'])
    print('tx', tx_hash, flush=True)

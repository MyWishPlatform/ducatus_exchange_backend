import time
import random

from web3 import Web3, HTTPProvider

from random_contract.contract_settings import ABI, GAS_LIMIT, AVERAGE_BLOCK_TIME, BLOCKS_DELTA
from ducatus_exchange.settings_local import CONTRACT_ADDRESS
from ducatus_exchange.settings import NETWORK_SETTINGS

w3 = Web3(HTTPProvider(f'http://{NETWORK_SETTINGS["DUCX"]["host"]}:{NETWORK_SETTINGS["DUCX"]["port"]}'))
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)


def get_tx_base_params():
    tx_params = {
        'nonce': w3.eth.getTransactionCount(NETWORK_SETTINGS['DUCX']['address'], 'pending'),
        'gasPrice': w3.eth.gasPrice,
        'gas': GAS_LIMIT,
    }

    return tx_params


def sign_and_send_tx(tx_data):
    signed = w3.eth.account.signTransaction(tx_data, NETWORK_SETTINGS['DUCX']['private'])
    tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)

    return tx_hash.hex()


def init_lottery(tickets_amount):
    tx_params = get_tx_base_params()

    initial_tx = contract.functions.setLotteryParams(BLOCKS_DELTA, tickets_amount).buildTransaction(tx_params)
    initial_tx_hash = sign_and_send_tx(initial_tx)

    return initial_tx_hash


def draw_numbers():
    tx_params = get_tx_base_params()

    draw_tx = contract.functions.determineWinner().buildTransaction(tx_params)
    draw_tx_hash = sign_and_send_tx(draw_tx)

    return draw_tx_hash


def get_numbers():
    first_number = contract.functions.firstNumber().call()
    #second_number = contract.functions.secondNumber().call()
    #third_number = contract.functions.thirdNumber().call()

    #return (first_number, second_number, third_number,)
    return (first_number)

def finalize_lottery(tickets_amount):
    print(f'generated future block delta: {BLOCKS_DELTA}', flush=True)

    init_tx_hash = init_lottery(tickets_amount)
    print('lottery initialized in contract', init_tx_hash, flush=True)

    future_blocks_timeout = BLOCKS_DELTA * AVERAGE_BLOCK_TIME
    print(f'waiting future blocks... sleep {future_blocks_timeout} seconds', flush=True)
    time.sleep(future_blocks_timeout)
    drawing_tx_hash = draw_numbers()
    print('lottery has drawn', drawing_tx_hash, flush=True)

    next_block_timeout = AVERAGE_BLOCK_TIME
    print(f'waiting next block... sleep {next_block_timeout} seconds', flush=True)
    time.sleep(next_block_timeout)

    #result = (0, 0, 0,)
    result=(0,)
    #while result == (0, 0, 0,):
    while result == (0,):
        result = get_numbers()
        print(f'lottery result {result}', flush=True)
        time.sleep(AVERAGE_BLOCK_TIME)

    return result

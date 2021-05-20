import os
import sys
import time
import traceback
from datetime import datetime

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ducatus_exchange.settings')

django.setup()

from ducatus_exchange.stats.models import StatisticsTransfer
from ducatus_exchange.settings_local import STATS_CHECKER_TIMEOUT
from ducatus_exchange.stats.stats_api import DucatusAPI, DucatusXAPI
from ducatus_exchange.stats.LastBlockPersister import get_last_block, save_last_block


def save_transfer(value, time, network):
    transfer = StatisticsTransfer(transaction_time=time, transaction_value=value, currency=network)
    transfer.save()


# Показывает транзакции из блоков, с учетом времени, сложно описать на словах, проще спросить лично
def update_stats(api, network):
    api = api
    CURRENT_BLOCK = get_last_block(network)
    STOP_BLOCK = api.get_last_blockchain_block()  # Отличается от функции выше только этой строкой
    tx_list = api.get_transactions_from_blocks(CURRENT_BLOCK, STOP_BLOCK)
    for tx in tx_list:
        normalized_time = datetime.strptime(tx.get('blockTime'), '%Y-%m-%dT%H:%M:%S.%fZ')
        save_transfer(api.get_tx_value(tx), normalized_time, network)
    return STOP_BLOCK


if __name__ == '__main__':
    duc_api = DucatusAPI()
    ducx_api = DucatusXAPI()
    while True:
        last_DUC_block = update_stats(duc_api, 'DUC')
        print(last_DUC_block)
        save_last_block('DUC', last_DUC_block)

        last_DUCX_block = update_stats(ducx_api, 'DUCX')
        print(last_DUCX_block)
        save_last_block('DUCX', last_DUCX_block)

        time.sleep(STATS_CHECKER_TIMEOUT)

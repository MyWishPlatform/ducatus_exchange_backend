import os
import sys
import time
import traceback
from datetime import timedelta, datetime

import django

from ducatus_exchange.settings_local import STATS_CHECKER_TIMEOUT
from ducatus_exchange.stats.DUC_blockchain_stats import get_transactions_from_blocks, get_last_block_time, \
    get_last_DUC_blockchain_block
from ducatus_exchange.stats.DUCX_blockchain_stats import get_last_DUCX_blockchain_block
from ducatus_exchange.stats.LastBlockPersister import save_last_DUC_block, save_last_DUCX_block, get_last_DUC_block, \
    get_last_DUCX_block

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ducatus_exchange.settings')

django.setup()

from ducatus_exchange.stats.models import DUC_StatisticsTransfer, DUCX_StatisticsTransfer


def get_DUC_transactions_count_and_sum():
    CURRENT_BLOCK = get_last_DUC_block()
    STOP_BLOCK = get_last_DUC_blockchain_block
    count = 0
    sum = 0
    try:
        transactions = get_transactions_from_blocks(CURRENT_BLOCK, STOP_BLOCK)
        for transaction in transactions:
            if transaction.get('value') not in (0, -1):
                count += 1
                sum += transaction.get('value')
        current_time = transactions[-1].get('blockTime')
    except Exception as e:
        print('\n'.join(traceback.format_exception(*sys.exc_info())), flush=True)
        time.sleep(1000)

    print('saved ok', flush=True)

    return count, sum, current_time


def get_DUCX_transactions_count_and_sum():
    CURRENT_BLOCK = get_last_DUCX_block()
    STOP_BLOCK = get_last_DUCX_blockchain_block
    countX = 0
    sumX = 0
    try:
        transactions = get_transactions_from_blocks(CURRENT_BLOCK, STOP_BLOCK)
        for transaction in transactions:
            if transaction.get(int('value')) not in (0, -1):  # Мб не проканает
                countX += 1
                sumX += transaction.get('value')
        current_timeX = transactions[-1].get('blockTime')
    except Exception as e:
        print('\n'.join(traceback.format_exception(*sys.exc_info())), flush=True)
        time.sleep(1000)

    print('saved ok', flush=True)

    return countX, sumX, current_timeX


# Сделал на всякий случай, функция нигде не использвуется, по дефолту данные сохраняются в БД
# def save_stats() -> type(None):
#     stats = {'transaction_count': {'transaction_count': transaction_count},
#              'transaction_sum': {'transaction_sum': transaction_sum},
#              'transaction_time': {'transaction_time': transaction_time}}
#
#     with open('ducatus_exchange/stats/stats.json', 'w') as f:
#         json.dump(stats, f)


def save_DUC_transfer():
    transaction_count, transaction_sum, transaction_time = get_DUC_transactions_count_and_sum()
    transfer = DUC_StatisticsTransfer(transaction_count=transaction_count, transaction_time=transaction_time,
                                      transaction_sum=transaction_sum)
    transfer.save()


def save_DUCX_transfer():
    transaction_countX, transaction_sumX, transaction_timeX = get_DUCX_transactions_count_and_sum()
    transfer = DUCX_StatisticsTransfer(transaction_countX=transaction_countX, transaction_timeX=transaction_timeX,
                                       transaction_sumX=transaction_sumX)
    transfer.save()


# Показывает транзакции из блоков, с учетом времени, сложно описать на словах, проще спросить лично
def show_update_DUC():
    CURRENT_BLOCK = get_last_DUC_block()
    STOP_BLOCK = get_last_DUCX_blockchain_block()
    value = 0
    counter = 0
    transaction_sum = 0
    tx_list = get_transactions_from_blocks(CURRENT_BLOCK, STOP_BLOCK)
    for l in tx_list:
        transaction_sum += value
        counter += 1
        last_block_time = get_last_block_time()
        # print(l, last_block_time, timedelta)
        normalized_time = datetime.strptime(l.get('blockTime'), '%Y-%m-%dT%H:%M:%S.%fZ')
        if normalized_time > last_block_time + timedelta(hours=2):
            save_DUC_transfer()
            value = 0
            counter = 0
        return STOP_BLOCK


def show_update_DUCX():
    CURRENT_BLOCK = get_last_DUCX_block()
    STOP_BLOCK = get_last_DUCX_blockchain_block()  # Отличается от функции выше только этой строкой
    value = 0
    counter = 0
    transaction_sum = 0
    tx_list = get_transactions_from_blocks(CURRENT_BLOCK, STOP_BLOCK)
    for l in tx_list:
        transaction_sum += value
        counter += 1
        last_block_time = get_last_block_time()
        # print(l, last_block_time, timedelta)
        normalized_time = datetime.strptime(l.get('blockTime'), '%Y-%m-%dT%H:%M:%S.%fZ')
        if normalized_time > last_block_time + timedelta(hours=2):
            save_DUCX_transfer()
            value = 0
            counter = 0
        return STOP_BLOCK


if __name__ == '__main__':
    # block = show()
    while True:
        last_DUC_block = show_update_DUC()
        print(last_DUC_block)
        save_last_DUC_block(last_DUC_block)

        last_DUCX_block = show_update_DUCX()
        print(last_DUCX_block)
        save_last_DUCX_block(last_DUCX_block)

        time.sleep(STATS_CHECKER_TIMEOUT)

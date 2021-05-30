import os
import sys
import time
import traceback
from datetime import datetime
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ducatus_exchange.settings')

django.setup()

from ducatus_exchange.stats.models import StatisticsAddress, StatisticsTransfer
from ducatus_exchange.settings_local import STATS_CHECKER_TIMEOUT
from ducatus_exchange.settings import STATS_NORMALIZED_TIME
from ducatus_exchange.ducatus_api import DucatusAPI, DucatusXAPI
from ducatus_exchange.stats.LastBlockPersister import get_last_block, save_last_block


def save_transfer(api, tx, network):
    normalized_time = datetime.strptime(tx.get('blockTime'), STATS_NORMALIZED_TIME)
    value = api.get_tx_value(tx)

    net_account_from = None
    net_account_to = None
    if network == 'DUCX':
        try:
            address_from = tx.get('from'.lower())
            net_account_from, new_from = StatisticsAddress.objects.get_or_create(user_address=tx.get('from'), network=network)
            net_account_from.balance = api.get_address_balance(net_account_from.user_address)
            net_account_from.save()

            address_to = tx.get('to').lower()
            if address_to != address_from:
                net_account_to, new_to = StatisticsAddress.objects.get_or_create(user_address=tx.get('to'), network=network)
                net_account_to.balance = api.get_address_balance(net_account_to.user_address)
                net_account_to.save()
            else:
                net_account_to = net_account_from
        except Exception as e:
            print('could not save addresses pack: {from_addr} and {to_addr}'.format(
                from_addr=tx.get('from').lower(),
                to_addr=tx.get('from'.lower())
            ), flush=True)
            print(e, flush=True)

    transfer = StatisticsTransfer.objects.filter(tx_hash=tx.get('txid'))
    transfer_saved = False
    if not transfer:
        transfer = StatisticsTransfer(
            transaction_time=normalized_time,
            transaction_value=value,
            tx_hash=tx.get('txid'),
            currency=network,
            address_from=net_account_from,
            address_to=net_account_to,
            fee_amount=tx.get('fee')
        )
        transfer.save()
        transfer_saved = True
    else:
        print('transfer already saved at obj id {tr_id}, hash {tr_hash}'.format(
            tr_id=transfer.first().id, tr_hash=tx.get('txid')),
            flush=True
        )

    return {
        'address_from': net_account_from.user_address if net_account_from else None,
        'address_to': net_account_to.user_address if net_account_to else None,
        'transfer_saved': transfer_saved
    }


def update_stats(api, network):
    last_saved_block = get_last_block(network)
    current_network_block = api.get_last_blockchain_block()

    current_block = last_saved_block
    addresses_in_txes = []
    while current_block <= current_network_block:
        txs_in_block = api.get_block_transactions(current_block)
        if len(txs_in_block) > 0:
            for tx in txs_in_block:
                transfer_info = save_transfer(api, tx, network)
                if network == 'DUCX' and transfer_info.get('transfer_saved'):
                    addresses_in_txes.append(transfer_info.get('address_from'))
                    addresses_in_txes.append(transfer_info.get('address_to'))

        print(f'Chain: {network}; Block: {current_block}, tx count: {len(txs_in_block)}')
        current_block += 1

    return {'current_block': current_block, 'transfer_addresses': addresses_in_txes}


def update_ducx_balances(api, addresses):
    c = 0
    for addr in addresses:
        try:
            account = StatisticsAddress.objects.get(user_address=addr)
            balance_before = account.balance
            account.balance = api.get_address_balance(account.user_address)
            account.save()
            c += 1
            print('account {acc} updated ({count}/{total}), balance now: {now}, was: {before}'.format(
                acc=account.user_address,
                count=c,
                total=len(addresses),
                now=account.balance,
                before=balance_before
            ), flush=True)
            # print(f'account {account.user_address} updated ({c}/{len(addresses)}), balance now: {account.balance}',
            #       flush=True)
        except Exception as e:
            print(f'Skipped address {addr} because of error', flush=True)
            print(f'Error: {e}', flush=True)


if __name__ == '__main__':
    duc_api = DucatusAPI()
    ducx_api = DucatusXAPI()
    while True:
        stats_duc_info = update_stats(duc_api, 'DUC')
        print(stats_duc_info.get('current_block'), flush=True)
        save_last_block('DUC', stats_duc_info.get('current_block'))

        stats_ducx_info = update_stats(ducx_api, 'DUCX')
        print(f'{stats_ducx_info.get("current_block")}', flush=True)
        save_last_block('DUCX', stats_ducx_info.get('current_block'))

        # takes some time, around 12 minutes for 21k addresse
        ducx_addresses = set(stats_ducx_info.get('transfer_addresses'))
        print(f'Updating current balances for {len(ducx_addresses)} addresses', flush=True)
        update_ducx_balances(ducx_api, ducx_addresses)
        print('Current balances of DUCX updated', flush=True)

        time.sleep(STATS_CHECKER_TIMEOUT)

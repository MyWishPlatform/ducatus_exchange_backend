import os
import time
import logging
from datetime import datetime
from argparse import ArgumentParser
import django
from concurrent.futures import ThreadPoolExecutor


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ducatus_exchange.settings')

django.setup()

from ducatus_exchange.stats.models import StatisticsAddress, StatisticsTransfer
from ducatus_exchange.settings_local import STATS_CHECKER_TIMEOUT
from ducatus_exchange.settings import STATS_NORMALIZED_TIME
from ducatus_exchange.ducatus_api import DucatusAPI, DucatusXAPI
from ducatus_exchange.stats.LastBlockPersister import get_last_block, save_last_block

logger = logging.getLogger('stats_checker')


def save_transfer(api, tx, network):
    normalized_time = datetime.strptime(tx.get('blockTime'), STATS_NORMALIZED_TIME)
    value = api.get_tx_value(tx)

    net_account_from = None
    net_account_to = None

    if network == 'DUCX':
        try:
            address_from = tx.get('from').lower()
            net_account_from, new_from = StatisticsAddress.objects.get_or_create(
                                                                    user_address=tx.get('from'),
                                                                    network=network)
            net_account_from.balance = api.get_address_balance(net_account_from.user_address)
            net_account_from.save()

            address_to = tx.get('to').lower()
            if address_to != address_from:
                net_account_to, new_to = StatisticsAddress.objects.get_or_create(
                                                                    user_address=tx.get('to'),
                                                                    network=network)
                net_account_to.balance = api.get_address_balance(net_account_to.user_address)
                net_account_to.save()
            else:
                net_account_to = net_account_from
        except Exception as e:
            logger.error(msg='could not save addresses pack: {from_addr} and {to_addr}'.format(
                from_addr=tx.get('from').lower(),
                to_addr=tx.get('from'.lower())
            ))
            logger.error(msg=e)

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
        logger.info(msg='transfer already saved at obj id {tr_id}, hash {tr_hash}'.format(
            tr_id=transfer.first().id,
            tr_hash=tx.get('txid'))
        )

    return {
        'address_from': net_account_from.user_address if net_account_from else None,
        'address_to': net_account_to.user_address if net_account_to else None,
        'transfer_saved': transfer_saved
        }

def update_address_balance(network, api, addr):
    if network == 'DUCX':
        account = StatisticsAddress.objects.get(user_address=addr)
    else:
        # network == 'DUC'
        account, new_duc_addr = StatisticsAddress.objects.get_or_create(
            user_address=addr, network=network)

    balance_before = account.balance
    account.balance = api.get_address_balance(account.user_address)
    account.save()
    return account, balance_before

def update_balances(network, api, addresses):
    c = 0
    if network not in ['DUC', 'DUCX']:
        raise Exception(f'network is not supported to update balances')

    def update_address(addr):
        nonlocal c
        try:
            account, balance_before = update_address_balance(network, api, addr)
            c += 1
            logger.info(
                '{net} STATS: account {acc} updated ({count}/{total}), balance now: {now}, was: {before}'.format(
                    net=network,
                    acc=account.user_address,
                    count=c,
                    total=len(addresses),
                    now=account.balance,
                    before=balance_before
                ))

        except Exception as e:
            logger.error(f'Skipped address {addr} because of error')
            logger.error(f'Error: {e}')

    with ThreadPoolExecutor() as executor:
        executor.map(update_address, addresses)
        
def update_balances_all():
    for network in ['DUC', 'DUCX']:
        addresses = StatisticsAddress.objects.filter(network=network).exclude(user_address__in=['False', 'false']).exclude(user_address=None)
        if network == 'DUC':
            api = DucatusAPI()
        else:
            api = DucatusXAPI()
        update_balances(network=network, api=api, addresses=addresses)


def update_stats(api, network):
    last_saved_block = get_last_block(network)
    current_network_block = api.get_last_blockchain_block()
    logger.info(f'saved block: {last_saved_block}, current: {current_network_block}')

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
                elif network == 'DUC':
                    addresses_in_single_tx = api.get_tx_addresses(tx.get('txid'))
                    for duc_addr in addresses_in_single_tx:
                        addresses_in_txes.append(duc_addr)
        logger.info(msg=f'Chain: {network}; Block: {current_block}, tx count: {len(txs_in_block)}')
        current_block += 1
        save_last_block(network, current_block)
        if current_block > (current_network_block - 1000):
            # update balances only when reaching full sync to network
            update_balances(network, api, set(addresses_in_txes))

    return {'current_block': current_block}


if __name__ == '__main__':
    arg_parser = ArgumentParser()
    arg_parser.add_argument('--network', help='specify network where checker runs (DUC/DUCX')
    arg_parser.add_argument('--balances', help='run balances updater', action="store_true")
    launch_args = arg_parser.parse_args()
    
    if launch_args.balances and not launch_args.network:
        while True:
            logger.info('run update balances')
            update_balances_all()
            logger.info('update balances done')
            time.sleep(STATS_CHECKER_TIMEOUT)

    if launch_args.network not in ['DUC', 'DUCX']:
        raise Exception('Checker can be launched only on DUC or DUCX network')

    stats_api = DucatusAPI() if launch_args.network == 'DUC' else DucatusXAPI()

    while True:
        stats_info = update_stats(stats_api, launch_args.network)
        logger.info(stats_info.get('current_block'))

        time.sleep(STATS_CHECKER_TIMEOUT)

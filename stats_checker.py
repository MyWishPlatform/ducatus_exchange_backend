import os
import time
import logging
from datetime import datetime
from argparse import ArgumentParser
import django

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
            address_from = tx.get('from'.lower())
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


def update_balances(api, addresses):
    c = 0
    for addr in addresses:
        try:
            account = StatisticsAddress.objects.get(user_address=addr)
            balance_before = account.balance
            account.balance = api.get_address_balance(account.user_address)
            account.save()
            c += 1
            logger.info('DUCX STATS: account {acc} updated ({count}/{total}), balance now: {now}, was: {before}'.format(
                acc=account.user_address,
                count=c,
                total=len(addresses),
                now=account.balance,
                before=balance_before
            ))
            # print(f'account {account.user_address} updated ({c}/{len(addresses)}), balance now: {account.balance}',
            #       flush=True)
        except Exception as e:
            logger.error(f'Skipped address {addr} because of error')
            logger.error(f'Error: {e}')


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
                elif network == 'DUC':
                    addresses_in_txes = api.get_tx_addresses(tx.get('txid'))
                    for duc_address in addresses_in_txes:
                        duc_addr, new_addr = StatisticsAddress.objects.get_or_create(
                            user_address=duc_address, network=network)
                        duc_addr.balance = api.get_address_balance(duc_addr.user_address)
                        duc_addr.save()
                        print('DUC STATS: account {acc} saved/updated, balance now: {now}'.format(
                            acc=duc_addr.user_address,
                            now=duc_addr.balance,
                        ), flush=True)

        logger.info(msg=f'Chain: {network}; Block: {current_block}, tx count: {len(txs_in_block)}')
        current_block += 1
        save_last_block(network, current_block)
        if network == "DUCX":
            update_balances(api, set(addresses_in_txes))

    return {'current_block': current_block}


if __name__ == '__main__':
    arg_parser = ArgumentParser()
    arg_parser.add_argument('network', help='specify network where checker runs (DUC/DUCX')
    launch_args = arg_parser.parse_args()

    if launch_args.network not in ['DUC', 'DUCX']:
        raise Exception('Checker can be launched only on DUC or DUCX network')

    stats_api = DucatusAPI() if launch_args.network is 'DUC' else DucatusXAPI()

    while True:
        stats_info = update_stats(stats_api, launch_args.network)
        logger.info(stats_info.get('current_block'))

        time.sleep(STATS_CHECKER_TIMEOUT)

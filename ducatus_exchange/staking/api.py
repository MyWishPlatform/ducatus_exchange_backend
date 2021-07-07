import os
import csv
from django.utils import timezone
from django.db.models import Sum
from ducatus_exchange.staking.models import DepositInput
from ducatus_exchange.consts import DECIMALS, DIVIDENDS_INFO


def export_deposit_statistics():
    unspent_inputs = DepositInput.objects.filter(spent_tx_hash=None, deposit__dividends__gt=0)

    if not unspent_inputs:
        print('All deposits has been withdrawn, nothing to export', flush=True)

    stat_fn = f'staking-{str(timezone.now().date())}.csv'
    with open(os.path.join(os.getcwd(), stat_fn), 'w') as csvfile:
        writer = csv.writer(csvfile)
        for deposit_input in unspent_inputs:
            writer.writerow(
                [
                    deposit_input.mint_tx_hash,
                    deposit_input.amount / DECIMALS['DUC'],
                    str(timezone.datetime.utcfromtimestamp(deposit_input.deposit.cltv_details.lock_time))
                ]
            )

    print(f'Export completed for {unspent_inputs.count()} transactions', flush=True)

    for month_count, percentage in DIVIDENDS_INFO.items():
        total = unspent_inputs.filter(deposit__dividends=percentage).aggregate(Sum('amount'))['amount__sum']
        total_in_duc = total / DECIMALS['DUC']
        print(f'{month_count} months: {total_in_duc} DUC')

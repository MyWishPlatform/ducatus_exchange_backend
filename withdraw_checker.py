import os
import sys
import time
import traceback
import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ducatus_exchange.settings')
import django

django.setup()

from django.utils import timezone

from ducatus_exchange.vouchers.models import FreezingVoucher
from ducatus_exchange.staking.models import Deposit, DepositInput
from ducatus_exchange.transfers.api import send_dividends
from ducatus_exchange.settings import WITHDRAW_CHECKER_TIMEOUT


class DucApiError(Exception):
    pass


def voucher_checker():
    vouchers_to_withdraw = FreezingVoucher.objects.filter(cltv_details__withdrawn=False)

    if not vouchers_to_withdraw:
        print('all vouchers have withdrawn at {}'.format(timezone.now()), flush=True)

    for voucher in vouchers_to_withdraw:
        lock_address = voucher.cltv_details.locked_duc_address

        print('lock address', lock_address, flush=True)
        all_voucher_inputs = voucher.voucherinput_set.all()
        if voucher.cltv_details.lock_time <= timezone.now().timestamp() and all_voucher_inputs and all(
                [voucher_input.spent_tx_hash for voucher_input in all_voucher_inputs]):
            voucher.cltv_details.withdrawn = True
            voucher.cltv_details.save()
            print('voucher with id {id} withdrawn at {time}'.format(id=voucher.id, time=timezone.now()), flush=True)
        elif all_voucher_inputs:
            print('not all inputs spent in voucher with id {id} at {time}'.format(id=voucher.id, time=timezone.now()),
                  flush=True)
        else:
            print('not any inputs in voucher with id {id} at {time}'.format(id=voucher.id, time=timezone.now()),
                  flush=True)


def deposit_checker():
    deposits_to_withdraw = Deposit.objects.filter(cltv_details__withdrawn=False)

    if not deposits_to_withdraw:
        print('all deposits have withdrawn at {}'.format(timezone.now()), flush=True)

    for deposit in deposits_to_withdraw:
        lock_address = deposit.cltv_details.locked_duc_address

        print('lock address', lock_address, flush=True)
        all_deposit_inputs = deposit.depositinput_set.all()
        if deposit.cltv_details.lock_time <= timezone.now().timestamp() and all_deposit_inputs and all(
                [deposit_input.spent_tx_hash for deposit_input in all_deposit_inputs]):
            try:
                first_input = DepositInput.objects.filter(deposit=deposit).order_by('minted_at').first()
                amount = int(first_input.amount * deposit.dividends/100 * deposit.cltv_details.total_days() / 365)
                print('calculated amount', amount, flush=True)
                if timezone.now() - first_input.minted_at >= datetime.timedelta(days=deposit.cltv_details.total_days()):
                    if amount != 0:
                        send_dividends(deposit.user_duc_address, amount)
                    else:
                        print(f'Does not send dividends for {deposit.user_duc_address} cause amount == 0')
                    deposit.cltv_details.withdrawn = True
                    deposit.cltv_details.save()
                    print('deposit with id {id} withdrawn at {time}'.format(id=deposit.id, time=timezone.now()),
                          flush=True)
                else:
                    print('deposit with id {id} not finalized yet'.format(id=deposit.id))
            except Exception as e:
                print('\n'.join(traceback.format_exception(*sys.exc_info())), flush=True)
        elif all_deposit_inputs:
            print('not all inputs spent in deposit with id {id} at {time}'.format(id=deposit.id, time=timezone.now()),
                  flush=True)
        else:
            print('not any inputs in deposit with id {id} at {time}'.format(id=deposit.id, time=timezone.now()),
                  flush=True)


if __name__ == '__main__':
    while True:
        print('\ndeposits checking at {}'.format(timezone.now()), flush=True)
        deposit_checker()
        print('\nvouchers checking at {}'.format(timezone.now()), flush=True)
        voucher_checker()
        time.sleep(WITHDRAW_CHECKER_TIMEOUT)

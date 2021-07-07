import os
import sys
import time
import json
import traceback
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ducatus_exchange.settings')
import django

django.setup()

from django.utils import timezone

from ducatus_exchange.vouchers.models import FreezingVoucher, VoucherInput
from ducatus_exchange.staking.models import Deposit, DepositInput
from ducatus_exchange.settings import INPUTS_CHECKER_TIMEOUT

DUC_API_URL = 'https://ducapi.rocknblock.io/api/DUC/mainnet/address/{duc_address}'


class DucApiError(Exception):
    pass


def voucher_inputs_checker():
    vouchers_to_withdraw = FreezingVoucher.objects.filter(cltv_details__withdrawn=False)

    if not vouchers_to_withdraw:
        print('all vouchers have withdrawn at {}'.format(timezone.now()), flush=True)

    for voucher in vouchers_to_withdraw:
        lock_address = voucher.cltv_details.locked_duc_address

        try:
            tx_inputs = json.loads(requests.get(DUC_API_URL.format(duc_address=lock_address)).content.decode())
        except Exception as e:
            print('\n'.join(traceback.format_exception(*sys.exc_info())), flush=True)
            continue

        for tx_input in tx_inputs:
            mint_tx_hash = tx_input['mintTxid']
            spent_tx_hash = tx_input['spentTxid']
            try:
                voucher_input = VoucherInput.objects.get(mint_tx_hash=mint_tx_hash)
                if not voucher_input.spent_tx_hash and spent_tx_hash:
                    voucher_input.spent_tx_hash = spent_tx_hash
                    voucher_input.spent_at = timezone.now()
            except VoucherInput.DoesNotExist:
                voucher_input = VoucherInput()
                voucher_input.voucher = voucher
                voucher_input.mint_tx_hash = mint_tx_hash
                voucher_input.tx_vout = tx_input['mintIndex']
                voucher_input.amount = tx_input['value']
                if spent_tx_hash:
                    voucher_input.spent_tx_hash = spent_tx_hash
                    voucher_input.spent_at = timezone.now()

            voucher_input.save()


def deposit_inputs_checker():
    deposits_to_withdraw = Deposit.objects.filter(cltv_details__withdrawn=False)

    if not deposits_to_withdraw:
        print('all deposits have withdrawn at {}'.format(timezone.now()), flush=True)

    for deposit in deposits_to_withdraw:
        lock_address = deposit.cltv_details.locked_duc_address

        try:
            tx_inputs = json.loads(requests.get(DUC_API_URL.format(duc_address=lock_address)).content.decode())
        except Exception as e:
            print('\n'.join(traceback.format_exception(*sys.exc_info())), flush=True)
            continue

        for tx_input in tx_inputs:
            mint_tx_hash = tx_input['mintTxid']
            spent_tx_hash = tx_input['spentTxid']
            try:
                deposit_input = DepositInput.objects.get(mint_tx_hash=mint_tx_hash)
                if not deposit_input.spent_tx_hash and spent_tx_hash:
                    deposit_input.spent_tx_hash = spent_tx_hash
                    deposit_input.spent_at = timezone.now()
            except DepositInput.DoesNotExist:
                deposit_input = DepositInput()
                deposit_input.deposit = deposit
                deposit_input.mint_tx_hash = mint_tx_hash
                deposit_input.tx_vout = tx_input['mintIndex']
                deposit_input.amount = tx_input['value']
                if spent_tx_hash:
                    deposit_input.spent_tx_hash = spent_tx_hash
                    deposit_input.spent_at = timezone.now()

            deposit_input.save()


if __name__ == '__main__':
    while True:
        print('\ndeposits checking at {}'.format(timezone.now()), flush=True)
        deposit_inputs_checker()
        print('\nvouchers checking at {}'.format(timezone.now()), flush=True)
        voucher_inputs_checker()
        time.sleep(INPUTS_CHECKER_TIMEOUT)

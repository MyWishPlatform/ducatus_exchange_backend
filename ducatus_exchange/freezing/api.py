import datetime
import os

from django.utils import timezone

from ducatus_exchange.freezing.models import CltvDetails
from ducatus_exchange.litecoin_rpc import DucatuscoreInterface
from ducatus_exchange.settings import BACKEND_PUBLIC_KEY
from ducatus_exchange.settings import CLTV_DIR
from ducatus_exchange.vtransfers.models import Transfer
from ducatus_exchange.vouchers.models import FreezingVoucher


def get_unused_frozen_vouchers(wallet_ids):
    vouchers = FreezingVoucher.objects.filter(wallet_id__in=wallet_ids, cltv_details__withdrawn=False,
                                              voucher__isnull=False)
    return vouchers


def save_cltv_data(frozen_at, redeem_script, locked_duc_address, user_public_key, lock_time, private_path):
    cltv_details = CltvDetails(
        lock_time=lock_time,
        redeem_script=redeem_script,
        locked_duc_address=locked_duc_address,
        user_public_key=user_public_key,
        frozen_at=frozen_at,
        private_path=private_path,
    )
    cltv_details.save()

    print('cltv generated', cltv_details.__dict__, flush=True)

    return cltv_details


def generate_cltv(receiver_public_key, lock_days, private_path, sender_pub_key=None):
    backend_public_key = BACKEND_PUBLIC_KEY if sender_pub_key is None else sender_pub_key
    frozen_at = timezone.now().replace(microsecond=0)
    lock_date = frozen_at + datetime.timedelta(days=lock_days)
    lock_time = int(lock_date.timestamp())

    bash_command = 'node {script_path} {receiver_public_key} {backend_public_key} {lock_time} {files_dir}' \
        .format(
        script_path=os.path.join(CLTV_DIR, 'cltv_generation.js'),
        receiver_public_key=receiver_public_key,
        backend_public_key=backend_public_key,
        lock_time=lock_time,
        files_dir=CLTV_DIR
    )
    if os.system(bash_command):
        raise Exception('error due redeem script generation')

    redeem_script_file = 'redeemScript-{}.txt'.format(lock_time)
    lock_address_file = 'lockAddress-{}.txt'.format(lock_time)

    with open(os.path.join(CLTV_DIR, redeem_script_file), 'r') as file:
        redeem_script = file.read()
    with open(os.path.join(CLTV_DIR, lock_address_file), 'r') as file:
        lock_address = file.read()

    os.remove(os.path.join(CLTV_DIR, redeem_script_file))
    os.remove(os.path.join(CLTV_DIR, lock_address_file))

    cltv_details = save_cltv_data(frozen_at, redeem_script, lock_address, receiver_public_key, lock_time, private_path)

    return cltv_details


def save_vout_number(transfer: Transfer):
    interface = DucatuscoreInterface()
    tx_data = interface.rpc.gettransaction(transfer.tx_hash)
    vout_number = tx_data['details'][0]['vout']
    transfer.vout_number = vout_number
    transfer.save()


def get_duc_transfer_fee():
    interface = DucatuscoreInterface()
    return interface.rpc.getinfo()['relayfee'] * 10 ** 8

import sys
import traceback

from ducatus_exchange.litecoin_rpc import DucatuscoreInterface
from ducatus_exchange.parity_interface import ParityInterface
from ducatus_exchange.transfers.models import DucatusTransfer
from ducatus_exchange.settings import ROOT_KEYS
from ducatus_exchange.bip32_ducatus import DucatusWallet
from ducatus_exchange.payments.models import Payment


def transfer_currency(payment):
    currency = payment.exchange_request.user.platform

    if currency == 'DUC':
        transfer_ducatus(payment)
    else:
        transfer_ducatusx(payment)


def transfer_ducatus(payment):
    amount = payment.sent_amount
    receiver = payment.exchange_request.user.address
    print('ducatus transfer started: sending {amount} DUC to {addr}'.format(amount=amount, addr=receiver), flush=True)
    currency = 'DUC'

    rpc = DucatuscoreInterface()
    tx = rpc.transfer(receiver, amount)
    transfer = save_transfer(payment, tx, amount, currency)

    print('ducatus transfer ok', flush=True)
    return transfer


def transfer_ducatusx(payment):
    amount = payment.sent_amount
    receiver = payment.exchange_request.user.address
    print('ducatusX transfer started: sending {amount} DUCX to {addr}'.format(amount=amount, addr=receiver), flush=True)
    currency = 'DUCX'

    parity = ParityInterface()
    tx = parity.transfer(receiver, amount)
    transfer = save_transfer(payment, tx, amount, currency)

    print('ducatusx transfer ok', flush=True)
    return transfer


def save_transfer(payment, tx, amount, currency):
    exchange_request = payment.exchange_request
    transfer = DucatusTransfer(
        exchange_request=exchange_request,
        tx_hash=tx,
        amount=amount,
        payment=payment,
        currency=currency,
        state='WAITING_FOR_CONFIRMATION'
    )
    transfer.save()

    print('transfer saved', flush=True)
    return transfer


def confirm_transfer(message):
    transfer_id = message['transferId']
    # transfer_address = message['address']
    transfer = DucatusTransfer.objects.get(id=transfer_id, state='WAITING_FOR_CONFIRMATION')
    print('transfer id {id} address {addr} '.format(id=transfer_id, addr=transfer.exchange_request.user.address),
          flush=True)
    # if transfer_address == transfer.request.duc_address:
    transfer.state = 'DONE'
    transfer.save()
    transfer.payment.transfer_state = 'DONE'
    transfer.payment.save()
    print('transfer completed ok')
    return


def collect_duc(payment):
    duc_root_key = DucatusWallet.deserialize(ROOT_KEYS['ducatus']['private'])
    duc_child = duc_root_key.get_child(payment.exchange_request.user.id, is_prime=False)
    child_private = duc_child.export_to_wif().decode()
    tx_hashes = [payment.tx_hash]
    address_from = payment.exchange_request.duc_address
    amount = payment.original_amount
    rpc = DucatuscoreInterface()
    address_to = rpc.rpc.getaccountaddress('')
    try:
        tx = rpc.internal_transfer(tx_hashes, address_from, address_to, amount, child_private)
        payment.collection_state = 'COLLECTED'
        payment.collection_tx_hash = tx
        payment.save()
    except Exception as e:
        print('Error in internal transfer from {addr_from} to {addr_to} with amount {amount} DUC'.format(
            addr_from=address_from,
            addr_to=address_to,
            amount=amount
        ), flush=True)
        print('\n'.join(traceback.format_exception(*sys.exc_info())), flush=True)
        payment.collection_state = 'ERROR'
        payment.save()

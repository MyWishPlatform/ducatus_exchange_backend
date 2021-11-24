# import time
import sys
import traceback
import logging
from decimal import Decimal

from ducatus_exchange.litecoin_rpc import DucatuscoreInterface
# from ducatus_exchange.parity_interface import ParityInterface
from ducatus_exchange.transfers.models import DucatusTransfer
from ducatus_exchange.settings import ROOT_KEYS, REF_BONUS_PERCENT, MINIMAL_RETURN
from ducatus_exchange.bip32_ducatus import DucatusWallet
# from ducatus_exchange.consts import DAYLY_LIMIT, WEEKLY_LIMIT
# from ducatus_exchange.payments.utils import calculate_amount
# from ducatus_exchange.exchange_requests.models import ExchangeRequest
from ducatus_exchange.ducatus_api import return_ducatus, return_ducatusx
# from ducatus_exchange.exchange_requests.models import ExchangeStatus

logger = logging.getLogger(__name__)


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

    logger.info(msg='transfer saved')
    return transfer


def make_ref_transfer(payment):
    amount = Decimal(int(int(Decimal(payment.sent_amount)) * REF_BONUS_PERCENT))
    receiver = payment.exchange_request.user.ref_address
    logger.info(msg=f'ducatus transfer started: sending {amount} DUC to {receiver}')
    currency = 'DUC'

    rpc = DucatuscoreInterface()
    tx = rpc.transfer(receiver, amount)
    transfer = save_transfer(payment, tx, amount, currency)

    logger.info(msg='ducatus referral transfer ok')
    return transfer


def transfer_ducatus(payment):
    amount = payment.sent_amount
    receiver = payment.exchange_request.user.address
    logger.info(msg=f'ducatus transfer started: sending {amount} DUC to {receiver}')
    currency = 'DUC'

    rpc = DucatuscoreInterface()
    # if not enough balance on admin address return tokens to user
    if rpc.get_balance() > amount:
        tx = rpc.transfer(receiver, amount)
        transfer = save_transfer(payment, tx, amount, currency)

        logger.info(msg='ducatus transfer ok')
        return transfer
    else:
        logger.info(msg=f'Not enough balance on wallet DUC, transaction with hash {payment.tx_hash} will return to user on DUCX')
        return_ducatusx(
            payment_hash=payment.tx_hash,
            amount=amount,
        )
        return None


# def transfer_ducatusx(payment):
#     amount = payment.sent_amount
#     receiver = payment.exchange_request.user.address
#     logger.info(msg=f'ducatusX transfer started: sending {amount} DUCX to {receiver}')
#     currency = 'DUCX'

#     parity = ParityInterface()
#     # if not enough balance on admin address return tokens to user
#     if parity.get_balance() > amount:
#         tx = parity.transfer(receiver, amount)
#         transfer = save_transfer(payment, tx, amount, currency)

#         logger.info(msg='ducatusx transfer ok')

#         time.sleep(100)    # small timeout in case of multiple payment messages
#         return transfer
#     else:
#         logger.info(msg=f'Not enough balance on wallet DUC, transaction with hash {payment.tx_hash} will return to user on DUCX')
#         return_ducatus(
#             payment_hash=payment.tx_hash,
#             amount=amount,
#         )
#         return None


def confirm_transfer(message):
    transfer_id = message['transferId']
    # transfer_address = message['address']
    transfer = DucatusTransfer.objects.get(id=transfer_id, state='WAITING_FOR_CONFIRMATION')
    logger.info(msg=f'transfer id {transfer_id} address {transfer.exchange_request.user.address}')
    # if transfer_address == transfer.request.duc_address:
    transfer.state_done()
    transfer.save()
    transfer.payment.state_transfer_done()
    transfer.payment.save()
    logger.info(msg='transfer completed ok')
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
        payment.state_collect_duc()
        payment.collection_tx_hash = tx
        payment.save()
    except Exception as e:
        logger.error(msg=f'Error in internal transfer from {address_from} to {address_to} with amount {amount} DUC')
        logger.error(msg=('\n'.join(traceback.format_exception(*sys.exc_info()))))
        payment.state_error_collect_duc()
        payment.save()

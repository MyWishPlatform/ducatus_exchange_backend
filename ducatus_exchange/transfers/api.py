import time
import sys
import traceback
import logging
from decimal import Decimal

from ducatus_exchange.litecoin_rpc import DucatuscoreInterface
from ducatus_exchange.parity_interface import ParityInterface, ParityInterfaceException
from ducatus_exchange.transfers.models import DucatusTransfer
from ducatus_exchange.settings import ROOT_KEYS, REF_BONUS_PERCENT, MINIMAL_RETURN
from ducatus_exchange.bip32_ducatus import DucatusWallet
from ducatus_exchange.consts import DAYLY_LIMIT, WEEKLY_LIMIT
from ducatus_exchange.payments.utils import calculate_amount
from ducatus_exchange.exchange_requests.models import ExchangeRequest
from ducatus_exchange.ducatus_api import return_ducatus, return_ducatusx
from ducatus_exchange.exchange_requests.models import ExchangeStatus

logger = logging.getLogger(__name__)


class TransferException(Exception):
    pass


def check_limits(payment):
    dayly_reserve = 0
    weekly_reserve = 0
    original_amount=payment.original_amount
    if payment.original_amount + payment.exchange_request.dayly_swap > DAYLY_LIMIT:
        dayly_reserve = DAYLY_LIMIT - payment.exchange_request.dayly_swap
        logger.info(msg=dayly_reserve)
        payment.original_amount = dayly_reserve
        if dayly_reserve <= 0:
            return False, original_amount
    if payment.original_amount + payment.exchange_request.weekly_swap > WEEKLY_LIMIT:
        weekly_reserve = WEEKLY_LIMIT - payment.exchange_request.weekly_swap
        if dayly_reserve > 0:
            payment.original_amount = min(dayly_reserve, weekly_reserve)
        else:
            payment.original_amount = weekly_reserve
        if weekly_reserve <= 0:
            return False, original_amount
    logger.info(msg=f' amount {payment.original_amount}')
    exchange_request=ExchangeRequest.objects.get(id=payment.exchange_request.id)
    exchange_request.dayly_swap += payment.original_amount
    exchange_request.weekly_swap += payment.original_amount
    exchange_request.save()
    logger.info(msg=f'daily {exchange_request.dayly_swap}')
    if payment.original_amount !=original_amount:
        payment.sent_amount, payment.rate = calculate_amount(payment.original_amount, payment.currency)
        logger.info(msg=f"User's {payment.exchange_request.user.id} sent_amount was recalculated due to limits")
        payment.save()
        return True, original_amount-payment.original_amount
    return True, 0


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

def transfer_ducatusx(payment):
    status = ExchangeStatus.objects.all().first().status
    if not status:
        logger.info(msg='exchange is disabled')
        return_ducatus(payment.tx_hash, payment.original_amount)
        return

    allowed, return_amount = check_limits(payment)

    if return_amount > MINIMAL_RETURN:
        return_ducatus(payment.tx_hash, return_amount)

    if not allowed:
        logger.info(
            msg=f"User's {payment.exchange_request.user.id} swap amount reached limits, cancelling transfer"
        )
        return

    amount = payment.sent_amount
    receiver = payment.exchange_request.user.address
    parity = ParityInterface()
    try:
        if parity.get_balance() > amount:
            logger.info(msg=f'ducatusX transfer started: sending {amount} DUCX to {receiver}')
            
            tx = parity.transfer(receiver, amount)
            transfer = save_transfer(payment, tx, amount, 'DUCX')
            
            logger.info(msg='ducatusx transfer ok')
            time.sleep(100) #  small timeout in case of multiple payment messages
            logger.info(msg='transfer completed')
            
            return transfer
        else:
            logger.info(msg=f'Not enough balance on wallet DUC, transaction with hash {payment.tx_hash} will return to user on DUCX')
            return_ducatus(payment_hash=payment.tx_hash,amount=amount,)
    except ParityInterfaceException as e:
        payment.state_transfer_error()
        payment.save()
        raise TransferException(e)
       

def add_transfer_duc_in_queue(payment):
    payment.state_transfer_in_queue()
    payment.save()


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

from ducatus_exchange.settings import MINIMAL_RETURN
from ducatus_exchange.ducatus_api import return_ducatus
from ducatus_exchange.exchange_requests.models import ExchangeStatus
from ducatus_exchange.payments.api import check_limits
from ducatus_exchange.payments.models import Payment
from ducatus_exchange.transfers.api import make_ref_transfer, transfer_ducatus


def send_duc_on_queue():

    payment_in_process = Payment.objects.filter(transfer_state='IN_PROCESS').first()
    if payment_in_process:
        return 
    payment = Payment.objects.filter(transfer_state='IN_QUEUE').first()
    if payment:
        # starting to send DUC
        
        if payment.exchange_request.user.platform == 'DUC':
            # first case when vaucher was created
            if payment.exchange_request.user.address.startswith('voucher') and \
                payment.exchange_request.user.ref_address:
                make_ref_transfer(payment)
            # second case when we just need to send DUC
            if not payment.exchange_request.user.address.startswith('voucher'):
                transfer_ducatus(payment)
        elif payment.exchange_request.user.platform == 'DUCX':
            _, return_amount = check_limits(payment)

            # third case when we try to transfer_ducx but status not exist
            if not ExchangeStatus.objects.first().status:
                return_ducatus(payment.tx_hash, payment.original_amount)
            # fourth case when we try to transfer_ducx but amount > MINIMAL_RETURN
            elif return_amount > MINIMAL_RETURN:
                return_ducatus(payment.tx_hash, return_amount)
            #  case when we try to transfer_ducx but wallet_balance + fee < amount
            else :
                return_ducatus(payment.tx_hash, payment.send_amount)
        payment.state_transfer_in_process()
        payment.save()

    return

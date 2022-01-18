from ducatus_exchange.settings import MINIMAL_RETURN
from ducatus_exchange.ducatus_api import return_ducatus
from ducatus_exchange.exchange_requests.models import ExchangeStatus
from ducatus_exchange.payments.api import check_limits
from ducatus_exchange.payments.models import Payment
from ducatus_exchange.transfers.api import make_ref_transfer, transfer_ducatus
from celery_config import app


@app.task
def process_queued_duc_transfer():
    pending_payments = Payment.objects.filter(
        transfer_state='PENDING',
        exchange_request__user__platform='DUC'
    ).first()
    if pending_payments:
        return 

    payment = Payment.objects.filter(transfer_state='QUEUED').first()
    if payment:
        user = payment.exchange_request.user     
        if user.platform == 'DUC':
            if user.address.startswith('voucher') and user.ref_address:
                make_ref_transfer(payment)
            if not user.address.startswith('voucher'):
                transfer_ducatus(payment)
        elif user.platform == 'DUCX':
            _, return_amount = check_limits(payment)

            if not ExchangeStatus.objects.first().status:
                return_ducatus(payment.tx_hash, payment.original_amount)
            elif return_amount > MINIMAL_RETURN:
                return_ducatus(payment.tx_hash, return_amount)
            else:
                return_ducatus(payment.tx_hash, payment.send_amount)
        else:
            raise ValueError('Platform is None')

    return

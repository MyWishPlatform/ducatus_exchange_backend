from ducatus_widget.litecoin_rpc import DucatuscoreInterface
from ducatus_widget.transfers.models import DucatusTransfer
from ducatus_widget.exchange_requests.models import ExchangeRequest


def transfer_ducatus(payment):
    amount = payment.sent_amount
    receiver = payment.to_addr
    print('ducatus transfer started: sending {amount} DUC to {addr}'.format(amount=amount, addr=receiver))

    rpc = DucatuscoreInterface()
    res = rpc.transfer(receiver, amount)

    exchange_request = ExchangeRequest.objects.get(id=payment.request.id)
    transfer = DucatusTransfer(
        request=exchange_request,
        # tx_hash=res['tx_hash']
        amount=amount,
        payment=payment,
        state='WAITING_FOR_CONFIRMATION'
    )
    transfer.save()

    print('ducatus transfer ok')
    return res

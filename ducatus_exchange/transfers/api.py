from ducatus_exchange.litecoin_rpc import DucatuscoreInterface
from ducatus_exchange.transfers.models import DucatusTransfer
from ducatus_exchange.exchange_requests.models import ExchangeRequest


def transfer_ducatus(payment):
    amount = payment.sent_amount
    receiver = payment.to_addr
    print('ducatus transfer started: sending {amount} DUC to {addr}'.format(amount=amount, addr=receiver))

    rpc = DucatuscoreInterface()
    tx = rpc.transfer(receiver, amount)

    exchange_request = ExchangeRequest.objects.get(id=payment.request.id)
    transfer = DucatusTransfer(
        request=exchange_request,
        tx_hash=tx,
        amount=amount,
        payment=payment,
        state='WAITING_FOR_CONFIRMATION'
    )
    transfer.save()

    print('ducatus transfer ok')
    return transfer


def confirm_transfer(message):
    # {
    #     "status": "COMMITTED",
    #     "transactionHash": "8c803aeb0fcaf3203b49bab742b5faf3be1c57b7bf6635b553f299b97bb7f626",
    #     "transferId": 51,
    #     "address": "Lraxrzhdo67f6MofLQRy91Y7t7TWsXpXEu4",
    #     "type": "transferred",
    #     "success": true
    # }
    transfer_id = message['transferId']
    transfer_address = message['ducAddress']
    print('transfer id {id} address {addr} '.format(id=transfer_id, addr=transfer_address))
    transfer = DucatusTransfer.objects.get(id=transfer_id, state='WAITING_FOR_CONFIRMATION')
    if transfer_address == transfer.request.duc_address:
        transfer.state = 'DONE'
        transfer.save()
    print('transfer completed ok')
    return

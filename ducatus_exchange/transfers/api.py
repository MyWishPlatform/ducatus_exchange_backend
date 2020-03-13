from ducatus_exchange.litecoin_rpc import DucatuscoreInterface
from ducatus_exchange.parity_interface import ParityInterface
from ducatus_exchange.transfers.models import DucatusTransfer
from ducatus_exchange.exchange_requests.models import ExchangeRequest


def transfer_currency(payment):
    currency = payment.exchange_request.to_currency

    if currency == 'DUC':
        transfer_ducatus(payment)
    else:
        transfer_ducatusx(payment)


def transfer_ducatus(payment):
    amount = payment.sent_amount
    receiver = payment.exchange_request.user.duc_address
    print('ducatus transfer started: sending {amount} DUC to {addr}'.format(amount=amount, addr=receiver), flush=True)

    rpc = DucatuscoreInterface()
    tx = rpc.transfer(receiver, amount)

    exchange_request = ExchangeRequest.objects.get(duc_address=payment.user.duc_address)
    transfer = DucatusTransfer(
        request=exchange_request,
        tx_hash=tx,
        amount=amount,
        payment=payment,
        state='WAITING_FOR_CONFIRMATION'
    )
    transfer.save()

    print('ducatus transfer ok', flush=True)
    return transfer


def transfer_ducatusx(payment):
    amount = payment.sent_amount
    receiver = payment.exchange_request.user.address
    print('ducatusX transfer started: sending {amount} DUC to {addr}'.format(amount=amount, addr=receiver), flush=True)

    parity = ParityInterface()



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
    print('transfer id {id} address {addr} '.format(id=transfer_id, addr=transfer_address), flush=True)
    transfer = DucatusTransfer.objects.get(id=transfer_id, state='WAITING_FOR_CONFIRMATION')
    if transfer_address == transfer.request.duc_address:
        transfer.state = 'DONE'
        transfer.save()
    print('transfer completed ok')
    return

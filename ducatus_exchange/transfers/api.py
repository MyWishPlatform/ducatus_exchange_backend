from ducatus_exchange.litecoin_rpc import DucatuscoreInterface
from ducatus_exchange.parity_interface import ParityInterface
from ducatus_exchange.transfers.models import DucatusTransfer


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

    print('ducatus transfer ok', flush=True)
    return transfer


def confirm_transfer(message):
    transfer_id = message['transferId']
    #transfer_address = message['address']
    transfer = DucatusTransfer.objects.get(id=transfer_id, state='WAITING_FOR_CONFIRMATION')
    print('transfer id {id} address {addr} '.format(id=transfer_id, addr=transfer.exchange_request.user.address), flush=True)
    #if transfer_address == transfer.request.duc_address:
    transfer.state = 'DONE'
    transfer.save()
    transfer.payment.transfer_state = 'DONE'
    print('transfer completed ok')
    return

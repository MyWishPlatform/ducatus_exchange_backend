from ducatus_widget.litecoin_rpc import DucatuscoreInterface


def transfer_ducatus(payment):
    amount = payment.sent_amount
    receiver = payment.to_addr
    print('ducatus transfer started: sending {amount} DUC to {addr}'.format(amount=amount, addr=receiver))

    rpc = DucatuscoreInterface()
    res = rpc.transfer(receiver, amount)
    print('ducatus transfer ok')
    return res

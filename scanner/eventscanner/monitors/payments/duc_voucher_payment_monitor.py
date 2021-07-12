from eventscanner.queue.pika_handler import send_to_backend
from mywish_models.models import VTransfer, session
from scanner.events.block_event import BlockEvent
from settings.settings_local import NETWORKS


class DucVoucherPaymentMonitor:
    network_type = ['DUCATUS_MAINNET']
    event_type = 'duc_transfer'

    @classmethod
    def on_new_block_event(cls, block_event: BlockEvent):
        if block_event.network.type not in cls.network_type:
            return

        addresses = block_event.transactions_by_address.keys()
        transfers = session \
            .query(VTransfer) \
            .filter(VTransfer.duc_address.in_(addresses)) \
            .distinct(VTransfer.duc_address)\
            .all()
        for transfer in transfers:
            transactions = block_event.transactions_by_address[transfer.duc_address]

            for transaction in transactions:
                for output in transaction.outputs:
                    if transfer.duc_address not in output.address:
                        print('{}: Found transaction out from internal address. Skip it.'
                              .format(block_event.network.type), flush=True)
                        continue

                    message = {
                        'txHash': transaction.tx_hash,
                        'currency': 'DUC',
                        'amount': output.value,
                        'success': True,
                        'status': 'COMMITTED'
                    }

                    send_to_backend(cls.event_type, NETWORKS[block_event.network.type]['queue'], message)

from abc import abstractmethod, ABC

from ducatus_exchange.litecoin_rpc import DucatuscoreInterface
from ducatus_exchange.parity_interface import ParityInterface
from ducatus_exchange.transfers.models import DucatusTransfer
from celery_config import app


@app.task
def confirm_transfers():
    transfers = DucatusTransfer.objects.filter(state='WAITING_FOR_CONFIRMATION').select_related('payment')

    if not transfers:
        return

    for transfer in transfers:
        tx_hash = transfer.tx_hash
        currency = transfer.currency
        fac = factory_creator(currency)

        conformation = fac.confirm(tx_hash)

        if conformation:
            transfer.state_done()
            transfer.save()
            transfer.payment.state_transfer_done()
            transfer.payment.save()


class TransferConformationAbstractFactory(ABC):

    @abstractmethod
    def confirm(self, tx_hash: str) -> bool:
        ...


class DUCTransferConformationFactory(TransferConformationAbstractFactory):

    def confirm(self, tx_hash: str) -> bool:
        rpc = DucatuscoreInterface()
        transaction = rpc.get_transaction(tx_hash)
        if transaction:
            return transaction.get('confirmations') > 5


class DUCXTransferConformationFactory(TransferConformationAbstractFactory):

    def confirm(self, tx_hash: str) -> bool:
        rpc = ParityInterface()
        transaction_block_number = rpc.get_block_for_transfer(tx_hash)
        total_block_number = rpc.get_block_count()
        if transaction_block_number:
            return (total_block_number - transaction_block_number) > 5


def factory_creator(currency: str) -> TransferConformationAbstractFactory:

    factories = {
        'DUC': DUCTransferConformationFactory(),
        'DUCX': DUCXTransferConformationFactory()
                 }

    return factories.get(currency)

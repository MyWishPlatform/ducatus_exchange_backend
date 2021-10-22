from logging import getLogger

from ducatus_exchange.parity_interface import ParityInterface
from ducatus_exchange.litecoin_rpc import DucatuscoreInterface

from .models import ExchangeStatus


def update_duc_and_ducx_balances():
    logger = getLogger('task')
    try:
        exchange_status = ExchangeStatus.objects.first()
        exchange_status.duc_balance = DucatuscoreInterface.get_balance()
        exchange_status.ducx_balance = ParityInterface.get_balance()
        exchange_status.save()
        logger(msg=f'Update DUC and DUCX balamces, everything is OK.')
        return
    except Exception as e:
        logger(msg=f'Cannot update DUC and DUCX balamces, something gone wrong wuth exception: \n {e}.')
        return
    
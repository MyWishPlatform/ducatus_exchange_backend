from logging import getLogger

from ducatus_exchange.parity_interface import ParityInterface
from ducatus_exchange.litecoin_rpc import DucatuscoreInterface

from .models import ExchangeStatus
from celery_config import app


@app.task
def update_duc_and_ducx_balances():
    logger = getLogger('task')
    status = ExchangeStatus.objects.first()
    status.duc_balance = DucatuscoreInterface().get_balance()
    status.ducx_balance = ParityInterface().get_balance()
    status.save()
    logger.info(msg=f'Update DUC and DUCX balances, everything is OK.')
    
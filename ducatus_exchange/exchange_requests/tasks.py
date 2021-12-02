from logging import getLogger

from ducatus_exchange.parity_interface import ParityInterface
from ducatus_exchange.litecoin_rpc import DucatuscoreInterface

from .models import ExchangeStatus
from celery_config import app


@app.task
def update_duc_and_ducx_balances():
    logger = getLogger('task')
    exchange_status = ExchangeStatus.objects.first()
    exchange_status.duc_balance = DucatuscoreInterface().get_balance()
    exchange_status.ducx_balance = ParityInterface().get_balance()
    exchange_status.save()
    logger.info(msg=f'Update DUC and DUCX balamces, everything is OK.')
    
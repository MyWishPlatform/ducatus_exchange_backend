from logging import getLogger

from ducatus_exchange.parity_interface import ParityInterface
from ducatus_exchange.bitcoin_api import DucatuscoreInterface
from ducatus_exchange.settings import NETWORK_SETTINGS
from ducatus_exchange.consts import DECIMALS

from .models import ExchangeStatus
from celery_config import app


@app.task
def update_duc_and_ducx_balances():
    logger = getLogger('task')
    status = ExchangeStatus.objects.first()
    duc_rpc = DucatuscoreInterface(NETWORK_SETTINGS["DUC"], DECIMALS["DUC"])
    status.duc_balance = duc_rpc.get_balance()
    status.ducx_balance = ParityInterface().get_balance()
    status.save()
    logger.info(msg=f'Update DUC and DUCX balances, everything is OK.')
    
from .models import StatisticsAddress
from ducatus_exchange.settings import DUCX_NODE_ADDRESSES
from ducatus_exchange.ducatus_api import DucatusXAPI
from stats_checker import update_balances

def update_nodes():
    ducx_api = DucatusXAPI()
    for node in DUCX_NODE_ADDRESSES:
        address = StatisticsAddress.objects.get_or_create(user_address=node, network='DUCX')
    update_balances(ducx_api, DUCX_NODE_ADDRESSES)

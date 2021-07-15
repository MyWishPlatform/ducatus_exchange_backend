import os
import logging

base_dir = 'ducatus_exchange/stats/last_block_info'

logger = logging.getLogger(__name__)


# взято отсюда https://github.com/MyWishPlatform/mywill_scanner/blob/lottery/scanner/services/last_block_persister.py
def get_last_block(network) -> int:
    try:
        with open(os.path.join(base_dir, f'{network}'), 'r') as file:
            last_block_number = file.read()
    except FileNotFoundError:
        return 1
    logger.info(msg=last_block_number)
    return int(last_block_number)


def save_last_block(network, last_block_number: int):
    with open(os.path.join(base_dir, f'{network}'), 'w') as file:
        file.write(str(last_block_number))
        logger.info(msg=last_block_number)

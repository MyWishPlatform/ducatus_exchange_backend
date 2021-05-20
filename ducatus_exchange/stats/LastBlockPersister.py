import os

base_dir = 'ducatus_exchange/stats'


# взято отсюда https://github.com/MyWishPlatform/mywill_scanner/blob/lottery/scanner/services/last_block_persister.py
def get_last_block(network) -> int:
    try:
        with open(os.path.join(base_dir, f'last_{network}_block_info'), 'r') as file:
            last_block_number = file.read()
    except FileNotFoundError:
        return 1
    print(last_block_number)
    return int(last_block_number)


def save_last_block(network, last_block_number: int):
    with open(os.path.join(base_dir, f'last_{network}_block_info'), 'w') as file:
        file.write(str(last_block_number))
        print(last_block_number)

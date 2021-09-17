import sys

from bip32utils import BIP32Key
from eth_keys import keys


def get_private_keys(root_private_key, child_id):
    root = BIP32Key.fromExtendedKey(root_private_key)
    eth_private = keys.PrivateKey(root.ChildKey(child_id).k.to_string())
    btc_private = root.ChildKey(child_id).WalletImportFormat()
    return eth_private, btc_private

if __name__ == '__main__':
    root_private_key = sys.argv[1]
    child_id = int(sys.argv[2])
    eth_private= get_private_keys(root_private_key, child_id)
    print(f'private keys for child with id {child_id}:\neth: {eth_private}', flush=True)
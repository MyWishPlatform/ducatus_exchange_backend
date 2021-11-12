import os
import csv
import datetime
import time

from ducatus_exchange.settings import BASE_DIR
from ducatus_exchange.litecoin_rpc import DucatuscoreInterface

time_format = '%Y-%m-%dT%H-%M-%S'


def batch(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]


def duc_airdrop(duc_amount):
    """
    Function to airdrop DUC to multiple addersses
    Utilises sendmany rpc call
    Argument 'duc_amount' expects number of DUC in int / float WITHOUT DECIMALS
    Example: duc_amount = 19.24 DUC
    Also in BASE_DIR must be file 'airdrop.csv' with Ducatus addresses, one adress on each line
    Will output file airdrop_out-(time).csv on execution finish
    """
    input_filename = 'airdrop.csv'
    current_time = datetime.datetime.now()
    output_filename = f'aidrop_out={str(datetime.datetime.strftime(current_time, time_format))}.csv'

    with open(os.path.join(BASE_DIR, output_filename), 'w') as outfile:
        airdrop_writer = csv.writer(outfile)
        with open(os.path.join(BASE_DIR, input_filename), 'r') as infile:
            airdrop_reader = csv.reader(infile)

            addresses = []

            for row in airdrop_reader:

                if not row:
                    # print('empty field')
                    continue
                else:
                    addresses.append(row[0])

            for address_batch in batch(addresses, 200):

                transfers = {}

                for duc_address in address_batch:

                    address_api = DucatuscoreInterface()
                    is_valid = address_api.rpc.validateaddress(duc_address)
                    # print(is_valid)
                    if is_valid.get('isvalid'):

                        transfers[duc_address] = duc_amount

                print('transfer', transfers)
                ducatus_api = DucatuscoreInterface()
                try:
                    ducatus_api.rpc.walletpassphrase(ducatus_api.settings['wallet_password'], 30)
                    transfer_hash = ducatus_api.rpc.sendmany("", transfers)
                    print(transfer_hash)
                except Exception as e:
                    print(e)
                    transfer_hash = 'transfer_error'

                for duc_address in address_batch:
                    airdrop_writer.writerow([duc_address, duc_amount, transfer_hash])

                time.sleep(60)



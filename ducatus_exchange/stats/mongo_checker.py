import pymongo
import json
import sys
import csv
import asyncio
import aiohttp
import traceback
from ducatus_exchange.settings import MONGO_CONNECTION

conn_str = MONGO_CONNECTION
client = pymongo.MongoClient(conn_str, serverSelectionTimeoutMS=5000)
pattern = [{"$match": {"network": "livenet"}}, {"$group": {"_id": "$walletId", "addresses": {"$addToSet": "$address"}}}]
database = client.bws
wallets = database.addresses.aggregate(pattern)
print(wallets)
URL = 'https://ducapi.rocknblock.io/api/DUC/mainnet/address/{}/balance'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def request_async(address):
    async with aiohttp.ClientSession() as session:
        async with session.get(URL.format(address)) as resp:
            res = await resp.text()
            return json.loads(res)['balance']


async def asynchronous(addresses):
    ioloop = asyncio.get_event_loop()
    tasks = [ioloop.create_task(request_async(address)) for address in addresses]
    return await asyncio.wait(tasks)


def get_duc_balances():
    res = []
    for ids, wallet in enumerate(wallets):
        try:
            amount = 0
            zp = list(zip(*[iter(wallet['addresses'])] * 100))
            for adrr in zp:
                result, pending = asyncio.run(asynchronous(adrr))
                amounts = [i.result() for i in result]
                if pending or len(adrr) != len(amounts):
                    print('fail')

                amount += sum(amounts)

                print('ok')

            result, pending = asyncio.run(asynchronous(wallet['addresses'][len(zp) * 50:]))
            amounts = [i.result() for i in result]
            if pending or len(wallet['addresses'][len(zp) * 50:]) != len(amounts):
                print('fail')

            amount += sum(amounts)

            res.append([wallet['_id'], amount])
            print(res[-1], ids)
        except:
            print('\n'.join(traceback.format_exception(*sys.exc_info())), flush=True)
            print()
            print('Exception with id {}'.format(ids))

    with open(os.path.join(BASE_DIR, 'DUC.csv'), 'w', newline='') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for i in res:
            if i[1] > 0:
                spamwriter.writerow([i[0], i[1]])

import pymongo
import json
import sys
import os
import asyncio
import aiohttp
import traceback
import logging

from ducatus_exchange.settings import MONGO_CONNECTION
from ducatus_exchange.stats.models import StatisticsAddress

logger = logging.getLogger(__name__)

conn_str = MONGO_CONNECTION
client = pymongo.MongoClient(conn_str, serverSelectionTimeoutMS=5000)
pattern = [{"$match": {"network": "livenet"}}, {"$group": {"_id": "$walletId", "addresses": {"$addToSet": "$address"}}}]
database = client.bws
wallets = database.addresses.aggregate(pattern)
logger.info(msg=wallets)
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
                    logger.info(msg='fail')

                amount += sum(amounts)

                logger.info(msg='ok')

            result, pending = asyncio.run(asynchronous(wallet['addresses'][len(zp) * 50:]))
            amounts = [i.result() for i in result]
            if pending or len(wallet['addresses'][len(zp) * 50:]) != len(amounts):
                logger.info(msg='fail')

            amount += sum(amounts)

            res.append([wallet['_id'], amount])
            logger.info(msg=(res[-1], ids))
            for i in res:
                if i[1] > 0:
                    StatisticsAddress.objects.update_or_create(user_address=i[0], balance=i[1], network='DUC')
        except:
            logger.error(msg=('\n'.join(traceback.format_exception(*sys.exc_info()))))
            logger.error(msg=f'Exception with id {ids}')

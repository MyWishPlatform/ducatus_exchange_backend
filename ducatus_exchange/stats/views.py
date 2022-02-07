# Create your views here.
from datetime import timedelta, datetime
import csv
import os
import logging

from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework import status

from ducatus_exchange.stats.models import StatisticsTransfer, StatisticsAddress, BitcoreAddress
from ducatus_exchange.stats.serializers import DucWalletsSerializer, BitcoreWalletsSerializer
from ducatus_exchange.settings import BASE_DIR
from ducatus_exchange.payments.models import Payment
from django.db.models import Sum
from ducatus_exchange.stats.models import DucatusAddressBlacklist

logger = logging.getLogger(__name__)


class DucToDucxSwap(APIView):
    """Summing dayly swap ducatus to ducatusx"""

    def get(self, request):
        time = datetime.now() - timedelta(hours=24)
        duc = Payment.objects.filter(currency='DUC', created_date__gt=time) \
            .aggregate(Sum('original_amount'))
        amount = duc['original_amount__sum']
        # because aggregator returns `None` if there is no objects after filtering
        amount = "0" if not amount else str(amount)
        return Response({
            'amount': amount,
            'currency': 'duc'
        }, status=status.HTTP_200_OK)


class DucxToDucSwap(APIView):
    """Summing dayly swap ducatusx to ducatus"""

    def get(self, request):
        time = datetime.now() - timedelta(hours=24)
        ducx = Payment.objects.filter(currency='DUCX', created_date__gt=time) \
            .exclude(exchange_request__duc_address__isnull=False) \
            .aggregate(Sum('original_amount'))
        amount = ducx['original_amount__sum']
        # because aggregator returns `None` if there is no objects after filtering
        amount = "0" if not amount else str(amount)
        return Response({
            'amount': amount,
            'currency': 'ducx'
        }, status=status.HTTP_200_OK)


class StatisticsTotals(APIView):
    """ Summing total amount in saved wallets """

    def get(self, request):
        duc_blacklist = DucatusAddressBlacklist.objects.filter(network='DUC').values('wallet_address')
        duc_address_sum = StatisticsAddress.objects.filter(network='DUC') \
            .exclude(user_address__in=duc_blacklist) \
            .aggregate(Sum('balance'))

        ducx_blacklist = DucatusAddressBlacklist.objects.filter(network='DUCX').values('wallet_address')
        ducx_address_sum = StatisticsAddress.objects.filter(network='DUCX') \
            .exclude(user_address__in=ducx_blacklist) \
            .aggregate(Sum('balance'))

        return Response({
            'duc': str(duc_address_sum['balance__sum']),
            'ducx': str(ducx_address_sum['balance__sum'])
        }, status=status.HTTP_200_OK)


class StatsHandler(APIView):
    def get(self, request, currency, days):
        data = []
        now = datetime.now()
        time = datetime.now() - timedelta(days=days)
        period = {1: 2, 7: 2, 30: 24, 365: 168}
        daily_txs = StatisticsTransfer.objects.filter(
            transaction_time__gt=now - timedelta(hours=24)) \
            .filter(transaction_time__lte=now) \
            .filter(currency=currency)
        weekly_txs = StatisticsTransfer.objects.filter(
            transaction_time__gt=now - timedelta(hours=24 * 7)) \
            .filter(transaction_time__lte=now) \
            .filter(currency=currency)
        daily_tx_count = daily_txs.count()
        weekly_txs_count = weekly_txs.count()
        daily_value = 0
        weekly_value = 0
        for tx in daily_txs:
            daily_value += tx.transaction_value
        for tx in weekly_txs:
            weekly_value += tx.transaction_value
        while time < now:
            statistics = StatisticsTransfer.objects.filter(
                transaction_time__gt=time) \
                .filter(transaction_time__lte=time + timedelta(hours=period[days])) \
                .filter(currency=currency)
            time += timedelta(hours=period[days])
            if time > now:
                time = now
            value = 0
            count = statistics.count()
            for stat in statistics:
                value += stat.transaction_value
            data.append({
                'value': value,
                'count': count,
                'time': time
            })
        return Response({
            'daily_value': daily_value,
            'daily_count': daily_tx_count,
            'weekly_value': weekly_value,
            'weekly_count': weekly_txs_count,
            'graph_data': data
        }, status=status.HTTP_200_OK)


class DucxWalletsViewSet(ReadOnlyModelViewSet):
    ducx_blacklist = DucatusAddressBlacklist.objects.filter(network='DUCX').values('wallet_address')
    queryset = StatisticsAddress.objects.filter(network='DUCX').exclude(user_address__in=ducx_blacklist)
    serializer_class = DucWalletsSerializer


class DucWalletsViewSet(ReadOnlyModelViewSet):
    duc_blacklist = DucatusAddressBlacklist.objects.filter(network='DUC').values('wallet_address')
    queryset = StatisticsAddress.objects.filter(network='DUC').exclude(user_address__in=duc_blacklist)
    serializer_class = DucWalletsSerializer


class BitcoreWalletsViewSet(ReadOnlyModelViewSet):
    duc_blacklist = DucatusAddressBlacklist.objects.filter(network='DUC').values('wallet_address')
    queryset = BitcoreAddress.objects.all().exclude(user_address__in=duc_blacklist)
    serializer_class = BitcoreWalletsSerializer


class DucWalletsToCSV(APIView):

    def get(self, request, currency):
        currency = currency.upper()
        if currency not in ['DUC', 'DUCX']:
            return Response('unknown currency', status=status.HTTP_400_BAD_REQUEST)

        account_list = []
        for account in StatisticsAddress.objects.filter(network=currency):
            account_list.append([account.user_address, account.balance])

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment;' \
                                          f' filename="{currency}_wallet_export_{str(datetime.now().date())}.csv"'
        writer = csv.DictWriter(response, fieldnames=['address', 'balance'])
        writer.writeheader()
        for acc in account_list:
            writer.writerow({'address': acc[0], 'balance': int(float(acc[1]))})


        return response

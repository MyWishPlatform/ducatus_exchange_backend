# Create your views here.
from datetime import timedelta, datetime
import csv
import os

from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework import status

from ducatus_exchange.stats.models import StatisticsTransfer, StatisticsAddress
from ducatus_exchange.stats.serializers import DucxWalletsSerializer
from ducatus_exchange.settings import BASE_DIR
from ducatus_exchange.transfers.models import DucatusTransfer, DucatusAddressBlacklist
from django.db.models import Sum


class DucToDucxSwap(APIView):
    def get(self, request):
        time = datetime.now() - timedelta(hours=24)
        duc = DucatusTransfer.objects.get(currency='DUC')\
            .exclude(
            exchange_request__duc_address__in=DucatusAddressBlacklist.objects.all().values('duc_wallet_address'))\
            .filter(created_date__gt=time)\
            .agreggate(Sum('amount'))
        return Response({
                'ammount': duc,
                'currency': 'duc'
                }, status=status.HTTP_200_OK)


class DucxToDucSwap(APIView):
    def get(self, request):
        time = datetime.now() - timedelta(hours=24)
        ducx = DucatusTransfer.objects.get(currency='DUCX')\
            .exclude(
            exchange_request__duc_address__isnull=False,
            exchange_request__ducx_address__in=DucatusAddressBlacklist.objects.all().values('ducx_wallet_address'))\
            .filter(created_date__gt=time)\
            .agreggate(Sum('amount'))
        return Response({
                'ammount': ducx,
                'currency': 'ducx'
                }, status=status.HTTP_200_OK)


class StatsHandler(APIView):
    def get(self, request, currency, days):
        data = []
        now = datetime.now()
        time = datetime.now() - timedelta(days=days)
        period = {1: 2, 7: 2, 30: 24, 365: 168}
        daily_txs = StatisticsTransfer.objects.filter(
                transaction_time__gt=now - timedelta(hours=24))\
            .filter(transaction_time__lte=now)\
            .filter(currency=currency)
        weekly_txs = StatisticsTransfer.objects.filter(
            transaction_time__gt=now - timedelta(hours=24*7))\
            .filter(transaction_time__lte=now)\
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
                transaction_time__gt=time).filter(transaction_time__lte=time+timedelta(hours=period[days])).filter(currency=currency)
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
    queryset = StatisticsAddress.objects.filter(network='DUCX')
    serializer_class = DucxWalletsSerializer


class DucxWalletsToCSV(APIView):

    def get(self, request, currency):
        if currency.lower() == 'ducx':
            account_list = []
            for account in StatisticsAddress.objects.filter(network='DUCX'):
                account_list.append([account.user_address, account.balance])

            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="ducx_wallet_export_{str(datetime.now().date())}.csv"'
            writer = csv.DictWriter(response, fieldnames=['ducx_address', 'balance'])
            writer.writeheader()
            for acc in account_list:
                writer.writerow({'ducx_address': acc[0], 'balance': int(float(acc[1]))})

        elif currency.lower() == 'duc':
            try:
                print(os.path.join(BASE_DIR, 'DUC.csv'))
                with open(os.path.join(BASE_DIR, 'DUC.csv'), 'r') as f:
                    file_data = f.read()
            except:
                return Response('currently calculating balances, please check again in a few hours')
            response = HttpResponse(file_data, content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="duc_wallet_export_{str(datetime.now().date())}.csv"'

        else:
            return Response('unknown currency', status=status.HTTP_400_BAD_REQUEST)

        return response


class DucWalletsView(APIView):
    def get(self, request):
        with open(os.path.join(BASE_DIR, 'DUC.csv'), 'r') as f:
            data = [{k: v for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True)]
        return Response(data, status=status.HTTP_200_OK)



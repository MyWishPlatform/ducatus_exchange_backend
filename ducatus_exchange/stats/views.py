# Create your views here.
from datetime import timedelta, datetime

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from ducatus_exchange.stats.models import StatisticsTransfer


class StatsHandler(APIView):
    def get(self, request, currency, days):
        data = []
        now = datetime.now()
        time = datetime.now() - timedelta(days=days)
        period = {1: 2, 7:2, 30:24}
        daily_txs = StatisticsTransfer.objects.filter(
                transaction_time__gt=now - timedelta(hours=24)).filter(transaction_time__lte=now).filter(currency=currency)
        weekly_txs = StatisticsTransfer.objects.filter(
            transaction_time__gt=now - timedelta(hours=24*7)).filter(transaction_time__lte=now).filter(currency=currency)
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

# Create your views here.
import datetime

from rest_framework.response import Response
from rest_framework.views import APIView

from ducatus_exchange.stats.models import StatisticsTransfer


class StatsHandler(APIView):
    def get(self, request, days):
        value = 0
        counter = 0
        data = []
        statistics = StatisticsTransfer.objects.filter(
            transaction_time__gte=datetime.datetime.now()-datetime.timedelta(days=days))
        for l in statistics:
            data.append({l.transaction_sum, l.transaction_count,
                         l.transaction_time})
        return Response(data)

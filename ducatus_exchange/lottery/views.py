from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser, AllowAny

from ducatus_exchange.lottery.models import Lottery
from ducatus_exchange.lottery.serializers import LotterySerializer


class LotteryViewSet(viewsets.ModelViewSet):
    queryset = Lottery.objects.all()
    serializer_class = LotterySerializer
    permission_classes = [AllowAny]

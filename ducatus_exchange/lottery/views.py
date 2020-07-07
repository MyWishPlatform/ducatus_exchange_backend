from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser, AllowAny, IsAuthenticatedOrReadOnly

from ducatus_exchange.lottery.models import Lottery, LotteryPlayer
from ducatus_exchange.lottery.serializers import LotterySerializer, LotteryPlayerSerializer


class LotteryViewSet(viewsets.ModelViewSet):
    queryset = Lottery.objects.all()
    serializer_class = LotterySerializer
    permission_classes = [AllowAny]


class LotteryPlayerViewSet(viewsets.ModelViewSet):
    queryset = LotteryPlayer.objects.all()
    serializer_class = LotteryPlayerSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

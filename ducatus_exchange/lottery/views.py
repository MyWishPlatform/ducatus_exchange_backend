import datetime

from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.exceptions import PermissionDenied

from ducatus_exchange.lottery.models import Lottery, LotteryPlayer
from ducatus_exchange.lottery.serializers import LotterySerializer, LotteryPlayerSerializer
from ducatus_exchange.settings import API_KEY


class LotteryViewSet(viewsets.ModelViewSet):
    queryset = Lottery.objects.all()
    serializer_class = LotterySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class LotteryPlayerViewSet(viewsets.ModelViewSet):
    queryset = LotteryPlayer.objects.order_by('id')
    serializer_class = LotteryPlayerSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


@api_view(http_method_names=['GET'])
def get_lotteries_info(request: Request):
    lotteries = Lottery.objects.all()
    return Response(LotterySerializer(many=True).to_representation(lotteries, with_description=False))


@api_view(http_method_names=['GET'])
def lottery_participants(request: Request):
    request_api_key = request.query_params.get('api_key')
    start_ts = int(request.query_params.get('start_ts', 0))
    end_ts = int(request.query_params.get('end_ts', datetime.datetime.now().timestamp()))
    if request_api_key != API_KEY:
        raise PermissionDenied
    lottery_players = LotteryPlayer.objects.all()
    serializer = LotteryPlayerSerializer()
    response_data = []
    for player in lottery_players:
        if player.transfer.created_date.timestamp() >= start_ts and player.transfer.created_date.timestamp() <= end_ts:
            response_data.append(serializer.to_representation(player, is_admin=True))

    return Response(response_data)

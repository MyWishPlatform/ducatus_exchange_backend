import datetime

from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.exceptions import PermissionDenied
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.pagination import PageNumberPagination

from ducatus_exchange.lottery.models import Lottery, LotteryPlayer
from ducatus_exchange.lottery.serializers import LotterySerializer, LotteryPlayerSerializer
from ducatus_exchange.lottery.manual_registration import register_payments_data
from ducatus_exchange.settings import API_KEY


class CustomizedPagination(PageNumberPagination):
    page_size = 10


class LotteryViewSet(viewsets.ModelViewSet):
    queryset = Lottery.objects.all()
    serializer_class = LotterySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class LotteryPlayerViewSet(viewsets.ModelViewSet):
    queryset = LotteryPlayer.objects.order_by('id')
    serializer_class = LotteryPlayerSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = CustomizedPagination

    def get_queryset(self):
        lottery_id = self.request.query_params.get('lottery_id')
        if lottery_id:
            queryset = LotteryPlayer.objects.filter(lottery__id=lottery_id).order_by('id')
            return queryset
        return LotteryPlayer.objects.order_by('id')

@api_view(http_method_names=['GET'])
def get_lottery_info(request: Request):
    lotteries = Lottery.objects.order_by('id').first()
    return Response(LotterySerializer().to_representation(lotteries, with_description=False))


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


@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'api_key': openapi.Schema(type=openapi.TYPE_STRING),
            'data': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'username': openapi.Schema(type=openapi.TYPE_STRING),
                        'quantity': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'package': openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            enum=[10, 50, 100, 500, 1000]
                        ),
                        'address': openapi.Schema(type=openapi.TYPE_STRING),
                        'email': openapi.Schema(type=openapi.TYPE_STRING),
                    },
                    required=['username', 'quantity', 'package', 'address', 'email']
                )
            )
        },
        required=['api_key', 'data']
    ),
)
@api_view(http_method_names=['POST'])
def register_payments_manually(request: Request):
    request_api_key = request.data.get('api_key')
    if request_api_key != API_KEY:
        raise PermissionDenied

    payments_data = request.data.get('data')

    register_payments_data(payments_data)

    return Response({'success': 'ok'})


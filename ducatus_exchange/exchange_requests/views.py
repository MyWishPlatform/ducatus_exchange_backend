from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from ducatus_exchange.exchange_requests.models import DucatusUser
from ducatus_exchange.exchange_requests.serializers import ExchangeRequestSerializer

exchange_response_duc = openapi.Response(
    description='Response with ETH, BTC, DUCX addresses if `DUC` passed in `to_currency`',
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'ducx_address': openapi.Schema(type=openapi.TYPE_STRING),
            'btc_address': openapi.Schema(type=openapi.TYPE_STRING),
            'eth_address': openapi.Schema(type=openapi.TYPE_STRING),
        },
    )
)

exchange_response_ducx = openapi.Response(
    description='Response with DUC addresses if `DUCX` passed in `to_currency`',
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'duc_address': openapi.Schema(type=openapi.TYPE_STRING)
        },
    )
)


class ExchangeRequest(APIView):

    @swagger_auto_schema(
        operation_description="post DUC or DUCX address and get addresses for payment",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['to_address', 'to_currency'],
            properties={
                'to_address': openapi.Schema(type=openapi.TYPE_STRING),
                'to_currency': openapi.Schema(type=openapi.TYPE_STRING)
            },
        ),
        responses={200: exchange_response_duc, 201: exchange_response_ducx},

    )
    def post(self, request):
        request_data = request.data
        address = request_data.get('to_address')
        platform = request_data.get('to_currency')

        ducatus_user_filter = DucatusUser.objects.filter(address=address, platform=platform)
        if not ducatus_user_filter:
            ducatus_user = DucatusUser(address=address, platform=platform)
            ducatus_user.save()
        else:
            ducatus_user = ducatus_user_filter.last()

        request_data['user'] = ducatus_user.id
        request_data.pop('to_address')

        print('data:', request_data, flush=True)
        serializer = ExchangeRequestSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()

        if platform == 'DUC':
            response_data = dict(serializer.data)
            response_data.pop('duc_address')
            response_data.pop('user')
        else:
            response_data = {'duc_address': serializer.data.get('duc_address')}

        print('res:', response_data)

        return Response(response_data, status=status.HTTP_201_CREATED)


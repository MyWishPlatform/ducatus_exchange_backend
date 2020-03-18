from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from ducatus_exchange.exchange_requests.models import DucatusUser, ExchangeRequest

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
        print('request data:', request_data, flush=True)
        address = request_data.get('to_address')
        platform = request_data.get('to_currency')

        ducatus_user_filter = DucatusUser.objects.filter(address=address, platform=platform)
        user_created = False
        if not ducatus_user_filter:
            user_created = True
            ducatus_user = DucatusUser(address=address, platform=platform)
            ducatus_user.save()
        else:
            ducatus_user = ducatus_user_filter.last()

        if user_created:
            exchange_request = ExchangeRequest(user=ducatus_user)
            exchange_request.save()
            exchange_request.generate_keys()
            exchange_request.save()
        else:
            exchange_request = ExchangeRequest.objects.get(user=ducatus_user)

        print('addresses:', exchange_request.__dict__, flush=True)

        if platform == 'DUC':
            response_data = {
                'eth_address': exchange_request.eth_address,
                'btc_address': exchange_request.btc_address,
                'ducx_address': exchange_request.ducx_address
            }
        else:
            response_data = {'duc_address': exchange_request.duc_address}

        print('res:', response_data)

        return Response(response_data, status=status.HTTP_201_CREATED)


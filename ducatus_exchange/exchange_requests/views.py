from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from ducatus_exchange.exchange_requests.models import DucatusUser
from ducatus_exchange.exchange_requests.serializers import ExchangeRequestSerializer
from ducatus_exchange.rates.api import convert_to_duc_single, get_usd_rates


class ExchangeRequest(APIView):

    @swagger_auto_schema(
        operation_description="post DUC address and get ETH and BTC addresses for payment",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['to_address', 'to_currency'],
            properties={
                'to_address': openapi.Schema(type=openapi.TYPE_STRING),
                'to_currency': openapi.Schema(type=openapi.TYPE_STRING)
            },
        ),
        responses={200: ExchangeRequestSerializer()},

    )
    def post(self, request):
        request_data = request.data
        address = request_data.get('to_address')
        platform = request_data.get('to_currency')

        ducatus_user, user_created = DucatusUser.objects.get_or_create(
            address=address,
            platform=platform
        )

        if user_created:
            ducatus_user.save()

        request_data['user'] = ducatus_user.id
        request_data.pop('to_address')

        print('data:', request_data, flush=True)
        serializer = ExchangeRequestSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()

        # rates = convert_to_duc_single(get_usd_rates())

        # obj.initial_rate_eth = float(rates['ETH'])
        # obj.initial_rate_btc = float(rates['BTC'])
        # obj.save()
        # print(obj.__dict__)

        if platform == 'DUC':
            response_data = dict(serializer.data)
            response_data.pop('duc_address')
            response_data.pop('user')
        else:
            response_data = {'duc_address': serializer.data.get('duc_address')}

        print('res:', response_data)

        return Response(response_data, status=status.HTTP_201_CREATED)


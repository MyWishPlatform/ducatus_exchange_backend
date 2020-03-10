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
            required=['address', 'platform'],
            properties={
                'address': openapi.Schema(type=openapi.TYPE_STRING),
                'platform': openapi.Schema(type=openapi.TYPE_STRING)
            },
        ),
        responses={200: ExchangeRequestSerializer()},

    )
    def post(self, request):
        print(request.data)
        serializer = ExchangeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()

        rates = convert_to_duc_single(get_usd_rates())

        obj.initial_rate_eth = float(rates['ETH'])
        obj.initial_rate_btc = float(rates['BTC'])
        obj.save()
        print(obj.__dict__)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

